import os
import sys
sys.path.append('/app')

import pandas as pd
import numpy as np
import pickle
from io import BytesIO
from datetime import datetime
import pytz
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


def load_preprocessor_and_model_from_s3(experiment_name: str, bucket: str = None):
    """
    S3에서 전처리 객체와 모델을 로드
    
    핵심: preprocessor.pkl에 전처리 로직이 모두 저장되어 있음!
    """
    if bucket is None:
        bucket = os.getenv('S3_BUCKET')
    
    s3_client = get_s3_client()
    
    # Preprocessor 로드 (전처리 로직 포함!)
    try:
        preprocessor_key = f"models/{experiment_name}/model_artifact/preprocessor.pkl"
        preprocessor_obj = s3_client.get_object(Bucket=bucket, Key=preprocessor_key)
        preprocessor = pickle.load(BytesIO(preprocessor_obj['Body'].read()))
        print(f"✅ Preprocessor 로드 완료 (fit된 전처리 객체)")
    except Exception as e:
        print(f"⚠️  Preprocessor 없음, 기존 방식 사용 필요")
        raise FileNotFoundError(f"Preprocessor not found: {e}")
    
    # 모델 로드
    model_key = f"models/{experiment_name}/model_artifact/model.pkl"
    model_obj = s3_client.get_object(Bucket=bucket, Key=model_key)
    model = pickle.load(BytesIO(model_obj['Body'].read()))
    print(f"✅ 모델 로드 완료")
    
    return preprocessor, model


def autobatch_predict(experiment_name: str = None, output_path: str = None):
    """
    완전 자동화된 배치 추론
    
    특징:
    - 전처리 로직 하드코딩 없음 ✅
    - S3에 저장된 preprocessor 객체 사용 ✅
    - DAG에서 전처리 변경 시 자동 적용 ✅
    
    Args:
        experiment_name: 모델명 (기본: 'weather-predictor-018')
        output_path: 결과 CSV 저장 경로 (옵션)
    
    Returns:
        result_df: 예측 결과 DataFrame
    """
    if experiment_name is None:
        experiment_name = os.getenv('DEFAULT_MODEL_NAME', 'weather-predictor-018')
    
    print(f"🚀 자동화 배치 추론 시작: {experiment_name}")
    print(f"💡 특징: 전처리 로직 하드코딩 없음, 완전 자동화!")
    
    # 1. S3에서 최신 데이터 로드
    df = get_latest_parquet_from_s3()
    
    # datetime을 서울 시간대(KST)로 변환
    kst = pytz.timezone('Asia/Seoul')
    if 'datetime' in df.columns:
        if df['datetime'].dt.tz is None:
            df['datetime'] = pd.to_datetime(df['datetime']).dt.tz_localize('UTC').dt.tz_convert(kst)
        else:
            df['datetime'] = df['datetime'].dt.tz_convert(kst)
        print(f"🕐 시간대 변환: UTC → KST (서울) | 샘플: {df['datetime'].iloc[0]}")
    
    # 메타데이터 저장 (예측 후 복원용)
    metadata_cols = ['datetime', 'station_id', 'region']
    metadata = df[metadata_cols].copy() if all(col in df.columns for col in metadata_cols) else None
    
    # 기상 데이터 저장 (결과에 포함)
    weather_cols = ['temperature', 'humidity', 'rainfall', 'pm10', 'wind_speed', 'pressure', 'region']
    weather_data = df[[col for col in weather_cols if col in df.columns]].copy()
    
    # 2. Preprocessor + Model 로드
    preprocessor, model = load_preprocessor_and_model_from_s3(experiment_name)
    
    # 3. 전처리 자동 적용! (하드코딩 없음!)
    print(f"🔧 전처리 자동 적용 (preprocessor.transform)")
    X_processed = preprocessor.transform(df)
    print(f"✅ 전처리 완료: {X_processed.shape}")
    
    # 4. 예측
    print(f"🤖 모델 예측 중...")
    predictions = model.predict(X_processed)
    print(f"✅ 예측 완료: {len(predictions)}개")
    
    # 5. 결과 생성
    result_df = pd.DataFrame()
    
    # 메타데이터 추가
    if metadata is not None:
        for col in metadata_cols:
            if col in metadata.columns:
                result_df[col] = metadata[col].values
    
    # 예측 결과 추가
    result_df['predicted_comfort_score'] = predictions
    
    # 기상 데이터 추가
    for col in weather_data.columns:
        result_df[col] = weather_data[col].values
    
    # 6. 결과 저장 (옵션)
    if output_path:
        result_df.to_csv(output_path, index=False)
        print(f"💾 결과 저장: {output_path}")
    
    print(f"🎉 자동화 배치 추론 완료!")
    print(f"🎯 예측된 쾌적지수: {predictions[0]:.1f}/100")
    
    # 통계 출력
    print(f"\n📊 예측 통계:")
    print(f"   평균: {predictions.mean():.1f}")
    print(f"   최소: {predictions.min():.1f}")
    print(f"   최대: {predictions.max():.1f}")
    
    return result_df


if __name__ == "__main__":
    import fire
    
    try:
        fire.Fire(autobatch_predict)
    except TypeError:
        # fire 라이브러리의 출력 에러 무시
        pass 