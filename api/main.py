import os
import sys
sys.path.append('/app')

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import numpy as np
from contextlib import asynccontextmanager

from src.utils.utils import get_s3_client
import boto3
import pickle
from io import BytesIO
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 전역 변수
model = None
scaler = None

class WeatherInput(BaseModel):
    """날씨 입력 데이터 모델"""
    temperature: float
    humidity: float
    pressure: float
    wind_speed: float
    wind_direction: float
    dew_point: float
    cloud_amount: float
    visibility: float
    season: str  # spring, summer, autumn, winter
    temp_category: str  # cold, mild, warm, hot, very_cold
    pm10_grade: str  # good, moderate, bad, very_bad
    region: str  # central, southern, unknown
    is_morning_rush: int = 0
    is_evening_rush: int = 0
    is_weekend: int = 0

def load_model_from_s3(experiment_name: str = None):
    """S3에서 최고 성능 모델과 스케일러 로드"""
    global model, scaler
    
    if experiment_name is None:
        experiment_name = os.getenv('DEFAULT_MODEL_NAME', 'weather-predictor-006')
    
    try:
        s3_client = get_s3_client()
        bucket = os.getenv('S3_BUCKET')
        
        # 모델 로드
        model_key = f"models/{experiment_name}/model_artifact/model.pkl"
        model_obj = s3_client.get_object(Bucket=bucket, Key=model_key)
        model = pickle.load(BytesIO(model_obj['Body'].read()))
        
        # 스케일러 로드
        scaler_key = f"models/{experiment_name}/model_artifact/scaler.pkl"
        scaler_obj = s3_client.get_object(Bucket=bucket, Key=scaler_key)
        scaler = pickle.load(BytesIO(scaler_obj['Body'].read()))
        
        print(f"✅ 모델 로드 성공: {experiment_name}")
        return True
        
    except Exception as e:
        print(f"❌ 모델 로드 실패: {e}")
        return False

def preprocess_input(data: WeatherInput):
    """입력 데이터 전처리 (split.py와 동일한 로직 적용)"""
    # DataFrame 생성
    df = pd.DataFrame([data.dict()])
    
    # 결측치 처리 (-99, -9를 NaN으로 변환 후 평균값 대체)
    X = df.replace([-99, -9], np.nan)
    numeric_cols = X.select_dtypes(include=[np.number]).columns
    X[numeric_cols] = X[numeric_cols].fillna(X[numeric_cols].mean())
    
    # 범주형 변수 원핫인코딩 (split.py와 동일)
    categorical_cols = ['season', 'temp_category', 'pm10_grade', 'region']
    categorical_cols = [col for col in categorical_cols if col in X.columns]
    
    if categorical_cols:
        X = pd.get_dummies(X, columns=categorical_cols, drop_first=True)
    
    return X

# 앱 시작/종료 시 리소스 관리
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 모델 로드
    load_model_from_s3()
    yield
    # 종료 시 정리 작업 (필요시)

app = FastAPI(
    title="Weather Comfort Score API", 
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
def root():
    return {
        "message": "Weather Comfort Score API 실행 중!",
        "model_loaded": model is not None,
        "scaler_loaded": scaler is not None
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model_status": "loaded" if model else "not_loaded",
        "scaler_status": "loaded" if scaler else "not_loaded"
    }

@app.post("/predict")
def predict(data: WeatherInput):
    """쾌적지수 예측"""
    if model is None or scaler is None:
        raise HTTPException(status_code=503, detail="모델 또는 스케일러가 로드되지 않았습니다")
    
    try:
        # 전처리
        processed_data = preprocess_input(data)
        
        # 스케일링
        scaled_data = scaler.transform(processed_data)
        
        # 예측
        prediction = model.predict(scaled_data)[0]
        
        return {
            "predicted_comfort_score": round(prediction, 2),
            "input_data": data.dict(),
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"예측 중 오류 발생: {str(e)}")

@app.get("/predict/example")
def predict_example():
    """예시 예측"""
    example_data = WeatherInput(
        temperature=20.5,
        humidity=65.0,
        pressure=1013.2,
        wind_speed=3.2,
        wind_direction=180.0,
        dew_point=15.3,
        cloud_amount=5.0,
        visibility=10000.0,
        season="spring",
        temp_category="mild",
        pm10_grade="good",
        region="central",
        is_morning_rush=0,
        is_evening_rush=0,
        is_weekend=1
    )
    
    return predict(example_data)

@app.post("/reload_model")
def reload_model(experiment_name: str = None):
    """모델 재로드"""
    success = load_model_from_s3(experiment_name)
    if success:
        model_name = experiment_name or os.getenv('DEFAULT_MODEL_NAME', 'weather-predictor-006')
        return {"message": f"모델 재로드 성공: {model_name}"}
    else:
        raise HTTPException(status_code=500, detail="모델 재로드 실패")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 