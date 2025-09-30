import os
import sys
sys.path.append('/app')

import pandas as pd
import numpy as np
import pickle
from io import BytesIO
from datetime import datetime
import requests
import traceback

from src.data.data_cleaning import (
    clean_weather_data,
    add_time_features,
    add_temp_features,
    add_air_quality_features,
    add_region_features
)
from src.utils.utils import get_s3_client

def get_realtime_weather_data():
    """실시간 기상청 API 데이터 수집 (main.py에서 가져온 함수)"""
    try:
        auth_key = os.getenv("WEATHER_API_KEY")
        
        if not auth_key:
            print("⚠️ WEATHER_API_KEY가 설정되지 않음")
            return None
            
        # 기상청 API Hub
        base_url = "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm2.php"
        
        params = {
            'authKey': auth_key,
            'stn': '108',  # 서울 관측소
            'schListCnt': 1,  # 최신 1개 데이터만
            'disp': 1         # JSON 형태
        }
        
        print(f"🌐 실시간 기상청 API 호출: {base_url}")
        response = requests.get(base_url, params=params, timeout=10)
        
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            if len(lines) > 1:
                # 헤더 제외하고 첫 번째 데이터 라인 파싱
                data_line = lines[1].split()
                
                if len(data_line) >= 10:
                    weather_data = {
                        'datetime': datetime.now(),
                        'station_id': '108',
                        'temperature': float(data_line[2]) if data_line[2] != '-9' else 20.0,
                        'humidity': float(data_line[5]) if data_line[5] != '-9' else 60.0,
                        'pressure': float(data_line[7]) if data_line[7] != '-9' else 1013.0,
                        'wind_speed': float(data_line[3]) if data_line[3] != '-9' else 3.0,
                        'wind_direction': float(data_line[4]) if data_line[4] != '-9' else 180.0,
                        'dew_point': float(data_line[6]) if data_line[6] != '-9' else 15.0,
                        'cloud_amount': float(data_line[8]) if data_line[8] != '-9' else 5.0,
                        'visibility': float(data_line[9]) if data_line[9] != '-9' else 10000.0,
                        'precipitation': 0.0,  # 기본값
                        'sunshine': 5.0,       # 기본값
                        'pm10': 30.0,          # 기본값
                        'pm10_grade': 'good',  # 기본값
                        'region': 'central'    # 서울 = central
                    }
                    
                    print(f"✅ 실시간 데이터 수집 완료")
                    return weather_data
        
        print(f"❌ API 응답 실패: {response.status_code}")
        return None
        
    except Exception as e:
        print(f"❌ 실시간 데이터 수집 실패: {e}")
        traceback.print_exc()
        return None

def load_model_from_s3(experiment_name: str, bucket: str = None):
    """S3에서 모델과 스케일러 로드"""
    if bucket is None:
        bucket = os.getenv('S3_BUCKET')
    
    s3_client = get_s3_client()
    
    # 모델 로드
    model_key = f"models/{experiment_name}/model_artifact/model.pkl"
    model_obj = s3_client.get_object(Bucket=bucket, Key=model_key)
    model = pickle.load(BytesIO(model_obj['Body'].read()))
    
    # 스케일러 로드
    scaler_key = f"models/{experiment_name}/model_artifact/scaler.pkl"
    scaler_obj = s3_client.get_object(Bucket=bucket, Key=scaler_key)
    scaler = pickle.load(BytesIO(scaler_obj['Body'].read()))
    
    return model, scaler

def preprocess_raw_data(df):
    """raw 데이터를 data_cleaning.py로 전처리"""
    print("🔧 data_cleaning.py 전처리 시작")
    
    # 1단계: 기본 정리 (data_cleaning.py)
    df = clean_weather_data(df)
    df = add_time_features(df)
    df = add_temp_features(df)
    df = add_air_quality_features(df)
    df = add_region_features(df)
    
    print("✅ data_cleaning.py 전처리 완료")
    return df

def preprocess_for_prediction(df):
    """split.py와 동일한 후처리 로직"""
    print("🔧 split.py 후처리 시작")
    
    # 타겟 제외
    target_col = "comfort_score"
    exclude_cols = [target_col, "pm10", "datetime", "station_id"]
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    X = df[feature_cols].copy()
    X = X.replace([-99, -9], np.nan)
    
    # 고결측 컬럼 제거
    high_missing_cols = []
    for col in X.columns:
        missing_ratio = X[col].isnull().sum() / len(X)
        if missing_ratio > 0.5:
            high_missing_cols.append(col)
    
    if high_missing_cols:
        print(f"고결측 컬럼 제거: {high_missing_cols}")
        X = X.drop(columns=high_missing_cols)
    
    # 결측치 평균 대체
    numeric_cols = X.select_dtypes(include=[np.number]).columns
    X[numeric_cols] = X[numeric_cols].fillna(X[numeric_cols].mean())
    
    # 원핫인코딩
    categorical_cols = ['season', 'temp_category', 'pm10_grade', 'region']
    categorical_cols = [col for col in categorical_cols if col in X.columns]
    
    if categorical_cols:
        print(f"원핫인코딩 적용: {categorical_cols}")
        X = pd.get_dummies(X, columns=categorical_cols, drop_first=True)
    
    print("✅ split.py 후처리 완료")
    return X

def batch_predict(input_path: str = None, use_realtime: bool = False, experiment_name: str = None, output_path: str = None):
    """배치 추론 실행 (raw 데이터 또는 실시간 데이터 처리)"""
    if experiment_name is None:
        experiment_name = os.getenv('DEFAULT_MODEL_NAME', 'weather-predictor-006')
    
    print(f"🔄 배치 추론 시작: {experiment_name}")
    
    # 1. 데이터 로드
    if use_realtime:
        print("📡 실시간 기상청 API 데이터 사용")
        realtime_data = get_realtime_weather_data()
        
        if realtime_data is None:
            raise ValueError("실시간 데이터를 가져올 수 없습니다. API 키와 네트워크를 확인하세요.")
        
        # 실시간 데이터를 DataFrame으로 변환
        df = pd.DataFrame([realtime_data])
        
    elif input_path:
        print(f"📂 Raw 데이터 로드: {input_path}")
        df = pd.read_csv(input_path)
        
    else:
        raise ValueError("input_path를 제공하거나 use_realtime=True로 설정하세요")
    
    print(f"데이터 로드: {df.shape}")
    print(f"컬럼: {list(df.columns)}")
    
    # 2. 모델 로드
    model, scaler = load_model_from_s3(experiment_name)
    print("✅ 모델 로드 완료")
    
    # 3. 전처리 (data_cleaning.py)
    df_processed = preprocess_raw_data(df)
    
    # 4. 후처리 (split.py)
    X = preprocess_for_prediction(df_processed)
    X_scaled = scaler.transform(X)  # ✅ transform만 사용
    print(f"최종 전처리 완료: {X_scaled.shape}")
    
    # 5. 예측
    predictions = model.predict(X_scaled)
    
    # 6. 결과 저장
    result_df = df_processed[['datetime', 'station_id']].copy()
    result_df['predicted_comfort_score'] = predictions
    
    if output_path:
        result_df.to_csv(output_path, index=False)
        print(f"✅ 결과 저장: {output_path}")
    
    print(f"🎉 배치 추론 완료: {len(predictions)}개 예측")
    print(f"🎯 예측된 쾌적지수: {predictions[0]:.1f}/100")
    
    return result_df

def predict_current_weather(experiment_name: str = None):
    """현재 실시간 날씨 기반 쾌적지수 예측 (간편 함수)"""
    return batch_predict(use_realtime=True, experiment_name=experiment_name)

if __name__ == "__main__":
    import fire
    
    # Fire로 여러 함수 노출
    fire.Fire({
        'batch_predict': batch_predict,
        'predict_current': predict_current_weather
    })