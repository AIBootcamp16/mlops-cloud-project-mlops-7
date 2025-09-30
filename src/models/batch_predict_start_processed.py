import os
import sys
sys.path.append('/app')

import pandas as pd
import numpy as np
import pickle
from io import BytesIO

from src.data.data_cleaning import (
    clean_weather_data,
    add_time_features,
    add_temp_features,
    add_air_quality_features,
    add_region_features
)
from src.utils.utils import get_s3_client

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

def batch_predict(input_path: str, experiment_name: str = None, output_path: str = None):
    """배치 추론 실행 (CSV 파일 처리)"""
    if experiment_name is None:
        experiment_name = os.getenv('DEFAULT_MODEL_NAME', 'weather-predictor-006')
    
    print(f"🔄 배치 추론 시작: {experiment_name}")
    
    # 1. Raw 데이터 로드
    print(f"📂 Raw 데이터 로드: {input_path}")
    df = pd.read_csv(input_path)
    
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

if __name__ == "__main__":
    import fire
    fire.Fire(batch_predict)