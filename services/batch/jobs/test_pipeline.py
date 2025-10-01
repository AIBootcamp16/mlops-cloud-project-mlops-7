import sys
import os

# 프로젝트 루트를 PYTHONPATH에 추가
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, project_root)

# services 디렉토리를 PYTHONPATH에 추가
services_path = os.path.join(project_root, 'services')
sys.path.insert(0, services_path)

import pandas as pd
from batch.jobs.fetch import get_latest_parquet_from_s3
from batch.jobs.infer import batch_predict
from batch.jobs.upsert import upsert_predictions

def test_full_pipeline():
    print("=" * 50)
    print("배치 추론 파이프라인 테스트 시작")
    print("=" * 50)
    
    # 1. 데이터 수집
    print("\n1. 데이터 수집...")
    df = get_latest_parquet_from_s3()
    print(f"데이터 shape: {df.shape}")
    print(f"컬럼: {df.columns.tolist()}")
    
    # 2. 추론
    print("\n2. 모델 추론...")
    result_df = batch_predict(df)
    print(f"추론 결과 shape: {result_df.shape}")
    print(f"예측값 샘플:\n{result_df.head()}")
    
    # 3. DB 저장
    print("\n3. DB 저장...")
    upsert_predictions(result_df)
    
    print("\n" + "=" * 50)
    print("테스트 완료!")
    print("=" * 50)

if __name__ == "__main__":
    test_full_pipeline()