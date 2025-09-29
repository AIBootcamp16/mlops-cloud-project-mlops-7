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
    """날씨 입력 데이터 모델 (app.py와 동일한 구조)"""
    temperature: float
    humidity: float
    pressure: float
    wind_speed: float
    wind_direction: float
    dew_point: float
    cloud_amount: float
    visibility: float
    season: str  # spring, summer, autumn, winter
    temp_category: str  # very_cold, cold, mild, warm, hot
    pm10_grade: str  # good, moderate, bad, very_bad
    region: str  # central, southern, unknown
    is_morning_rush: int = 0
    is_evening_rush: int = 0
    is_weekend: int = 0

def load_model_from_s3(experiment_name: str = None):
    """S3에서 최고 성능 모델과 스케일러 로드 """
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
    """입력 데이터 전처리 (기존 split.py 로직과 최대한 호환)"""
    # DataFrame 생성
    df = pd.DataFrame([data.dict()])
    
    # 노트북에서 확인한 추가 피처들을 기본값으로 생성 (유연하게 처리)
    try:
        # 기본값으로 누락 피처들 생성
        df['rainfall'] = -9.0  # 결측치로 처리됨 (고결측 컬럼이라 제거됨)
        df['sunshine'] = 5.0   # 기본값 (학습 시 사용된 피처이므로 유지)
        df['hour'] = 12  # 정오 기본값
        df['day_of_week'] = 1  # 월요일
        df['month'] = 6  # 6월
        df['is_rush_hour'] = data.is_morning_rush or data.is_evening_rush
        df['is_weekday'] = 1 - data.is_weekend
        
        # 온도 기반 파생 피처들
        df['temp_comfort'] = np.clip(20 - abs(data.temperature - 20), 0, 20)
        df['temp_extreme'] = 1 if (data.temperature < 0 or data.temperature > 35) else 0
        df['heating_needed'] = 1 if data.temperature < 10 else 0
        df['cooling_needed'] = 1 if data.temperature > 28 else 0
        
        # 미세먼지 기반 파생 피처
        df['mask_needed'] = 1 if data.pm10_grade in ['bad', 'very_bad'] else 0
        df['outdoor_activity_ok'] = 1 if data.pm10_grade in ['good', 'moderate'] else 0
        
        # 지역 기반 파생 피처
        df['is_metro_area'] = 1 if data.region == 'central' else 0
        df['is_coastal'] = 0  # 기본값
        
    except Exception as e:
        print(f"⚠️ 파생 피처 생성 중 오류: {e}")
    
    # 결측치 처리 (-99, -9를 NaN으로 변환 후 평균값 대체)
    X = df.replace([-99, -9], np.nan)
    numeric_cols = X.select_dtypes(include=[np.number]).columns
    X[numeric_cols] = X[numeric_cols].fillna(X[numeric_cols].mean())
    
    # 고결측 컬럼 제거 (기존 split.py 로직과 동일)
    high_missing_cols = []
    for col in X.columns:
        if col in ['rainfall', 'sunshine']:  # 노트북에서 확인한 고결측 컬럼들
            high_missing_cols.append(col)
    
    if high_missing_cols:
        X = X.drop(columns=high_missing_cols)
    
    # 범주형 변수 원핫인코딩 (기존 split.py와 동일)
    categorical_cols = ['season', 'temp_category', 'pm10_grade', 'region']
    categorical_cols = [col for col in categorical_cols if col in X.columns]
    
    if categorical_cols:
        X = pd.get_dummies(X, columns=categorical_cols, drop_first=True)
    
    # 실제 학습 시 사용된 37개 피처 (디버깅으로 확인한 정확한 리스트)
    expected_columns = [
        "temperature", "wind_speed", "humidity", "pressure", "wind_direction", "dew_point", 
        "cloud_amount", "visibility", "sunshine", "hour", "day_of_week", "month", 
        "is_morning_rush", "is_evening_rush", "is_rush_hour", "is_weekday", "is_weekend", 
        "temp_comfort", "temp_extreme", "heating_needed", "cooling_needed", "mask_needed", 
        "outdoor_activity_ok", "is_metro_area", "is_coastal", "season_spring", "season_summer", 
        "season_winter", "temp_category_hot", "temp_category_mild", "temp_category_very_cold", 
        "temp_category_warm", "pm10_grade_good", "pm10_grade_moderate", "pm10_grade_very_bad", 
        "region_southern", "region_unknown"
    ]
    
    # 누락된 컬럼들을 0으로 추가
    for col in expected_columns:
        if col not in X.columns:
            X[col] = 0
    
    # 학습 시와 동일한 순서로 컬럼 정렬
    X = X[expected_columns]
    
    return X

def convert_score_to_10_scale(score_100):
    """100점 척도를 10점 척도로 변환 (노트북 데이터 범위: 4.5~91.5)"""
    # 실제 데이터 범위에 맞춰 정규화 후 10점 척도로 변환
    min_score, max_score = 4.5, 91.5
    normalized = (score_100 - min_score) / (max_score - min_score)
    return normalized * 10

# 앱 시작/종료 시 리소스 관리
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 모델 로드
    load_model_from_s3()
    yield
    # 종료 시 정리 작업 (필요시)

app = FastAPI(
    title="Weather Comfort Score API", 
    version="0.1.0",
    description="AI 기반 날씨 쾌적지수 예측 API (0-10 척도)",
    lifespan=lifespan
)

@app.get("/")
def root():
    return {
        "message": "Weather Comfort Score API v0.1.0 실행 중!",
        "description": "AI 기반 날씨 쾌적지수 예측 (0-10 척도)",
        "model_loaded": model is not None,
        "scaler_loaded": scaler is not None,
        "endpoints": ["/predict", "/predict/example", "/health", "/reload_model"]
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model_status": "loaded" if model else "not_loaded",
        "scaler_status": "loaded" if scaler else "not_loaded",
        "api_version": "0.1.0"
    }

@app.post("/predict")
def predict(data: WeatherInput):
    """쾌적지수 예측 (0-10 척도)"""
    if model is None or scaler is None:
        raise HTTPException(status_code=503, detail="모델 또는 스케일러가 로드되지 않았습니다")
    
    try:
        # 전처리 (기존 시스템과 호환)
        processed_data = preprocess_input(data)
        
        # 스케일링 (피처 수가 맞지 않을 수 있으므로 유연하게 처리)
        try:
            scaled_data = scaler.transform(processed_data)
        except Exception as e:
            print(f"⚠️ 스케일링 오류: {e}")
            # 피처 수가 맞지 않는 경우, 기본적인 피처만 사용
            basic_features = ['temperature', 'humidity', 'pressure', 'wind_speed', 
                            'wind_direction', 'dew_point', 'cloud_amount', 'visibility',
                            'is_morning_rush', 'is_evening_rush', 'is_weekend']
            available_features = [col for col in basic_features if col in processed_data.columns]
            scaled_data = scaler.transform(processed_data[available_features])
        
        # 예측 (100점 척도)
        prediction_100 = model.predict(scaled_data)[0]
        
        # 10점 척도로 변환
        prediction_10 = convert_score_to_10_scale(prediction_100)
        
        # 범위 보정 (0-10)
        prediction_10 = np.clip(prediction_10, 0, 10)
        
        return {
            "predicted_comfort_score": round(prediction_10, 2),
            "raw_score_100": round(prediction_100, 2),  # 디버깅용
            "input_data": data.dict(),
            "status": "success",
            "scale": "0-10"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"예측 중 오류 발생: {str(e)}")

@app.get("/predict/example")
def predict_example():
    """예시 예측 (app.py의 기본값과 동일)"""
    example_data = WeatherInput(
        temperature=20.0,  # app.py 기본값
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
        return {
            "message": f"모델 재로드 성공: {model_name}",
            "api_version": "0.1.0",
            "scale": "0-10"
        }
    else:
        raise HTTPException(status_code=500, detail="모델 재로드 실패")

@app.get("/features/info")
def get_features_info():
    """피처 정보 반환 (실제 학습된 모델 정보 포함)"""
    # 실제 학습된 모델의 피처 정보
    actual_features = None
    n_features = None
    if scaler is not None:
        try:
            feature_names = getattr(scaler, 'feature_names_in_', None)
            n_features = getattr(scaler, 'n_features_in_', None)
            actual_features = feature_names.tolist() if feature_names is not None else None
        except:
            pass
    
    return {
        "note": "팀 시스템과 호환 모드 - 실제 학습된 모델 기준",
        "actual_n_features": n_features,
        "actual_feature_names": actual_features,
        "excluded_features": ["pm10", "datetime", "station_id", "comfort_score"],
        "high_missing_features": ["rainfall"],  # sunshine은 실제로 사용됨
        "categorical_features": ["season", "temp_category", "pm10_grade", "region"],
        "auto_generated_features": [
            "temp_comfort", "temp_extreme", "heating_needed", "cooling_needed",
            "mask_needed", "outdoor_activity_ok", "is_metro_area", "is_coastal"
        ],
        "scale_conversion": "100점 척도 → 10점 척도 (4.5~91.5 → 0~10)",
        "scaler_type": str(type(scaler).__name__) if scaler else None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 