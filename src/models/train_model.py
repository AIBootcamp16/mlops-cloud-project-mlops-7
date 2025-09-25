import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import joblib
import os

def train_weather_model():
    print("🤖 모델 학습 시작...")
    
    try:
        # 전처리된 데이터 로드
        df = pd.read_csv('data/processed/clean_weather.csv')
        print(f"데이터 로드 완료: {df.shape}")
    except:
        # 데이터가 없으면 더미 데이터 생성
        print("전처리 데이터가 없어서 더미 데이터 생성 중...")
        df = pd.DataFrame({
            'temperature': np.random.normal(25, 5, 100),
            'humidity': np.random.normal(65, 10, 100),
            'pressure': np.random.normal(1013, 5, 100)
        })
    
    # 피처와 타겟 분리 (예: 온도 예측)
    X = df[['humidity', 'pressure']].fillna(df.mean())
    y = df['temperature'].fillna(df['temperature'].mean())
    
    # 학습/테스트 분리
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 모델 학습
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)
    
    # 예측 및 평가
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    
    print(f"✅ 학습 완료!")
    print(f"MSE: {mse:.2f}")
    print(f"예측 예시: {y_pred[:3]}")
    
    # 모델 저장
    os.makedirs('models', exist_ok=True)
    joblib.dump(model, 'models/weather_model.pkl')
    print("💾 모델 저장 완료: models/weather_model.pkl")
    
    return model, mse

if __name__ == "__main__":
    train_weather_model()