import os
import sys
sys.path.append('/app')

import pandas as pd
from io import BytesIO

from src.utils.utils import get_s3_client

def get_latest_parquet_from_s3(bucket: str = None):
    """S3에서 최신 parquet 파일 자동 로드"""
    if bucket is None:
        bucket = os.getenv('S3_BUCKET')
    
    s3_client = get_s3_client()
    
    # ml_dataset/ 경로에서 최신 날짜 폴더 탐색
    prefix = "ml_dataset/predict/"
    
    # 모든 파일 목록 가져오기
    response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
    
    if 'Contents' not in response:
        raise FileNotFoundError(f"S3 경로에 파일이 없습니다: {prefix}")
    
    # parquet 파일만 필터링하고 최신순 정렬
    parquet_files = []
    for obj in response.get('Contents', []):
        key = obj['Key']
        size = obj.get('Size', 0)  # 대문자 'Size'
        
        # .parquet로 끝나고, 크기가 0보다 크고, .keep 파일이 아닌 것만
        if key.endswith('.parquet') and size > 0 and '.keep' not in key:
            parquet_files.append((obj['LastModified'], key, size))
            print(f"발견: {key} (크기: {size} bytes)")
    
    if not parquet_files:
        raise FileNotFoundError(f"S3에 유효한 parquet 파일이 없습니다. 경로: {prefix}")
    
    # 최신 파일 선택
    latest_file = sorted(parquet_files, reverse=True)[0][1]
    print(f"📂 최신 parquet 파일: {latest_file}")
    
    # S3에서 parquet 읽기
    obj = s3_client.get_object(Bucket=bucket, Key=latest_file)
    df = pd.read_parquet(BytesIO(obj['Body'].read()))
    
    print(f"✅ 데이터 로드 완료: {df.shape}")
    return df

