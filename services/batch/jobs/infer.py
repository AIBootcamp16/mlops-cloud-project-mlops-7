import os

import pandas as pd

from batch.jobs.load_model import load_model_from_s3
from batch.jobs.preprocess import preprocess_for_prediction


def batch_predict(df: pd.DataFrame) -> pd.DataFrame:

    # 1. 모델 로드
    model, scaler, config, feature_columns = load_model_from_s3()
    
    # 2. 저장할 메타 정보 + 원본 데이터 (DB에 필요한 컬럼들)
    save_cols = [
        'datetime', 'station_id',
        'temperature', 'humidity', 'rainfall', 
        'pm10', 'wind_speed', 'pressure'
    ]
    # 존재하는 컬럼만 선택
    available_cols = [col for col in save_cols if col in df.columns]
    meta_data = df[available_cols].copy()

    # 3. 전처리 (split.py 로직 + 컬럼 맞추기)
    X = preprocess_for_prediction(df, feature_columns)

    # 4. 스케일링
    X_scaled = scaler.transform(X)
    
    # 5. 추론
    predictions = model.predict(X_scaled)
    
    # 6. 결과 조합
    result_df = meta_data.copy()
    result_df['comfort_score'] = predictions
    result_df['model_name'] = config.get('model_name', 'unknown')
    result_df['model_version'] = os.getenv('CHAMPION_MODEL')
    
    print(f"🎉 배치 추론 완료: {len(predictions)}개 예측")
    print(f"🎯 예측된 쾌적지수: {predictions[0]:.1f}/100")
    
    return result_df

