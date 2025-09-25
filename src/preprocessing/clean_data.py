import pandas as pd
import numpy as np
import os

def clean_weather_data():
    print("🧹 데이터 전처리 시작...")
    
    # 더미 데이터 생성 (실제로는 S3나 파일에서 읽어옴)
    data = {
        'temperature': [25.5, 26.0, None, 24.8, 25.2],
        'humidity': [60, 65, 70, None, 58],
        'pressure': [1013.2, 1012.8, 1014.1, 1013.5, None]
    }
    df = pd.DataFrame(data)
    
    print(f"원본 데이터: {df.shape}")
    print(df.head())
    
    # 결측치 처리
    df_cleaned = df.fillna(df.mean())
    
    # 이상치 제거 (간단한 예시)
    df_cleaned = df_cleaned[df_cleaned['temperature'] > 0]
    
    print(f"\n전처리 후: {df_cleaned.shape}")
    print(df_cleaned.head())
    
    # 결과 저장
    os.makedirs('data/processed', exist_ok=True)
    df_cleaned.to_csv('data/processed/clean_weather.csv', index=False)
    
    print("✅ 전처리 완료! data/processed/clean_weather.csv 저장됨")
    return df_cleaned

if __name__ == "__main__":
    clean_weather_data()