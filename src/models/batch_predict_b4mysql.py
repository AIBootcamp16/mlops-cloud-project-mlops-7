import os
import sys
sys.path.append('/app')

import pandas as pd
import numpy as np
import pickle
import json
from io import BytesIO
from datetime import datetime
from src.utils.utils import get_s3_client

def get_latest_parquet_from_s3(bucket: str = None):
    """S3에서 최신 parquet 파일 자동 로드"""
    if bucket is None:
        bucket = os.getenv('S3_BUCKET')
    
    s3_client = get_s3_client()
    
    # ml_dataset/ 경로에서 최신 날짜 폴더 탐색
    prefix = "ml_dataset/"
    
    # 모든 파일 목록 가져오기
    response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
    
    # parquet 파일만 필터링하고 최신순 정렬
    parquet_files = []
    for obj in response.get('Contents', []):
        key = obj['Key']
        if key.endswith('.parquet'):
            parquet_files.append((obj['LastModified'], key))
    
    if not parquet_files:
        raise FileNotFoundError("S3에 parquet 파일이 없습니다")
    
    # 최신 파일 선택
    latest_file = sorted(parquet_files, reverse=True)[0][1]
    print(f"📂 최신 parquet 파일: {latest_file}")
    
    # S3에서 parquet 읽기
    obj = s3_client.get_object(Bucket=bucket, Key=latest_file)
    df = pd.read_parquet(BytesIO(obj['Body'].read()))
    
    print(f"✅ 데이터 로드 완료: {df.shape}")
    return df

def load_model_from_s3(experiment_name: str, bucket: str = None):
    """S3에서 모델, 스케일러, config, feature_columns 로드"""
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
    
    # config 로드
    config_key = f"models/{experiment_name}/config/train_config.json"
    config_obj = s3_client.get_object(Bucket=bucket, Key=config_key)
    config = json.load(config_obj['Body'])
    
    # feature_columns 로드
    feature_col_key = f"models/{experiment_name}/config/feature_columns.json"
    feature_col_obj = s3_client.get_object(Bucket=bucket, Key=feature_col_key)
    feature_columns = json.load(feature_col_obj['Body'])
    
    return model, scaler, config, feature_columns

def preprocess_for_prediction(df, feature_columns):
    """split.py와 동일한 후처리 로직 + 컬럼 맞추기"""
    print("🔧 전처리 시작")
    
    # 카테고리 이름 통일
    if 'pm10_grade' in df.columns:
        df['pm10_grade'] = df['pm10_grade'].replace({
            'unhealthy': 'bad',
            'very_unhealthy': 'very_bad'
        })

    # 타겟 제외
    target_col = "comfort_score"
    exclude_cols = [target_col, "pm10", "datetime", "station_id"]
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    X = df[feature_cols].copy()
    X = X.replace([-99, -9], np.nan)
    
    # 고결측 컬럼 제거 (50% 이상)
    high_missing_cols = [col for col in X.columns if X[col].isnull().sum() / len(X) > 0.5]
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
        print(f"원핫인코딩: {categorical_cols}")
        X = pd.get_dummies(X, columns=categorical_cols, drop_first=True)
    
    # 학습 시 컬럼에 맞춰 보정
    for col in feature_columns:
        if col not in X.columns:
            X[col] = 0
    X = X[feature_columns]  # 순서까지 동일하게
    
    print(f"✅ 전처리 완료: {X.shape}")
    return X

def batch_predict(experiment_name: str = None, output_path: str = None):
    """배치 추론 실행 (S3 최신 데이터 자동 로드)"""
    if experiment_name is None:
        experiment_name = os.getenv('DEFAULT_MODEL_NAME', 'weather-predictor-018')
    
    print(f"🔄 배치 추론 시작: {experiment_name}")
    
    # 1. S3에서 최신 parquet 파일 로드 (이미 전처리됨)
    df = get_latest_parquet_from_s3()
    
    # 2. 모델, 스케일러, config, feature_columns 로드
    model, scaler, config, feature_columns = load_model_from_s3(experiment_name)
    print(f"✅ 모델 로드 완료 (피처: {len(feature_columns)}개)")
    
    # 3. 전처리 (split.py 로직 + 컬럼 맞추기)
    X = preprocess_for_prediction(df, feature_columns)
    X_scaled = scaler.transform(X)
    
    # 4. 예측
    predictions = model.predict(X_scaled)
    
    # 5. 결과 저장
    result_df = df[['datetime', 'station_id']].copy()
    result_df['predicted_comfort_score'] = predictions
    
    if output_path:
        result_df.to_csv(output_path, index=False)
        print(f"✅ 결과 저장: {output_path}")
    
    print(f"🎉 배치 추론 완료: {len(predictions)}개 예측")
    print(f"🎯 예측된 쾌적지수: {predictions[0]:.1f}/100")
    
    return result_df

if __name__ == "__main__":
    import fire
    
    try:
        fire.Fire(batch_predict)
    except TypeError:
        # fire 라이브러리의 출력 에러 무시
        pass