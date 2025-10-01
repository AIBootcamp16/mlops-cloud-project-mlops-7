<<<<<<< HEAD
import os
import sys
sys.path.append('/app')

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import pytz

# batch_predict.py에서 예측 함수 import
from src.models.batch_predict import batch_predict

# MySQL 함수 import
from src.storage.mysql_client import query_prediction_by_datetime, save_prediction_to_mysql

from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

app = FastAPI(
    title="Weather Comfort Score API", 
    version="0.1.0",
    description="batch_predict.py 기반 쾌적지수 예측 API"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "Weather Comfort Score API v0.1.0 실행 중!",
        "description": "batch_predict.py 기반 쾌적지수 예측 API",
        "endpoints": ["/predict/now", "/predict/morning", "/predict/evening", "/health"]
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "api_version": "0.1.0"
    }

@app.get("/predict/{prediction_type}")
def get_comfort_score(prediction_type: str):
    """쾌적지수 예측 (캐시 우선 조회)"""
    if prediction_type not in ["now", "morning", "evening"]:
        raise HTTPException(status_code=400, detail="prediction_type은 now, morning, evening 중 하나여야 합니다")
    
    try:
        # 1. 현재 시간대 (정각 기준) - KST
        kst = pytz.timezone('Asia/Seoul')
        current_hour = datetime.now(kst).replace(minute=0, second=0, microsecond=0)
        
        # 2. MySQL에서 캐시 조회
        cached = query_prediction_by_datetime(current_hour)
        
        if cached:
            # ✅ 캐시 HIT
            print(f"✅ 캐시 HIT: {current_hour}")
            comfort_score = cached['comfort_score']
            weather_data = {
                'temperature': cached.get('temperature'),
                'humidity': cached.get('humidity'),
                'rainfall': cached.get('rainfall'),
                'pm10': cached.get('pm10'),
                'wind_speed': cached.get('wind_speed'),
                'pressure': cached.get('pressure'),
                'region': cached.get('region'),
                'station_id': cached.get('station_id')
            }
        else:
            # ❌ 캐시 MISS: 최초 예측
            print(f"🔄 캐시 MISS: {current_hour} 최초 예측")
            result_df = batch_predict(experiment_name='weather-predictor-018')
            
            # station_id 108번만 필터링
            station_108 = result_df[result_df['station_id'] == '108'].iloc[0]
            
            # MySQL에 저장 (전체 지역)
            save_prediction_to_mysql(result_df, current_hour)
            
            # 결과 추출 (station_id 108만)
            comfort_score = station_108['predicted_comfort_score']
            weather_data = {
                'temperature': station_108.get('temperature'),
                'humidity': station_108.get('humidity'),
                'rainfall': station_108.get('rainfall'),
                'pm10': station_108.get('pm10'),
                'wind_speed': station_108.get('wind_speed'),
                'pressure': station_108.get('pressure'),
                'region': station_108.get('region'),
                'station_id': station_108.get('station_id')
            }
        
        # 3. 응답 생성
        titles = {
            "now": "📱 현재 시점 예측",
            "morning": "🌅 출근길 예측 (6-9시)", 
            "evening": "🌆 퇴근길 예측 (18-21시)"
        }
        
        if comfort_score >= 80:
            label = "excellent"
            evaluation = "완벽한 날씨입니다! 🌟"
        elif comfort_score >= 60:
            label = "good" 
            evaluation = "쾌적한 날씨입니다! 😊"
        elif comfort_score >= 40:
            label = "fair"
            evaluation = "보통 날씨입니다 😐"
        else:
            label = "poor"
            evaluation = "날씨가 좋지 않습니다 ⚠️"
        
        return {
            "title": titles[prediction_type],
            "score": round(comfort_score, 1),
            "label": label,
            "evaluation": evaluation,
            "prediction_time": current_hour.strftime("%Y-%m-%d %H:%M"),
            "weather_data": weather_data,
            "prediction_type": prediction_type,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"예측 중 오류 발생: {str(e)}")

@app.get("/api/welcome")
def get_welcome_message():
    """시간대별 환영 메시지"""
    kst = pytz.timezone('Asia/Seoul')
    current_time = datetime.now(kst)
    hour = current_time.hour
    
    if 5 <= hour < 9:
        message = "좋은 아침이에요! 😊<br>오늘 하루도 화이팅입니다! ☀️"
    elif 9 <= hour < 12:
        message = "활기찬 오전이네요! 💪<br>오늘도 좋은 하루 되세요! ✨"
    elif 12 <= hour < 14:
        message = "점심시간이에요! 🍽️<br>맛있는 식사 하시고 힘내세요! 😋"
    elif 14 <= hour < 18:
        message = "근무하시느라 힘드시죠? 💼<br>조금만 더 힘내세요! 응원합니다! 📈"
    elif 18 <= hour < 22:
        message = "오늘도 고생 많으셨어요! 😊<br>푹 쉬시고 좋은 저녁 되세요! 🌆"
    else:
        message = "늦은 시간이네요! 🌙<br>푹 쉬시고 내일도 좋은 하루 되세요! 💤"
    
    return {
        "message": message,
        "current_time": current_time.strftime("%Y-%m-%d %H:%M"),
        "hour": hour
=======
from fastapi import FastAPI
import joblib
import numpy as np
import os

app = FastAPI(title="Weather ML API", version="1.0.0")

# 모델 로드 (전역 변수)
model = None

def load_model():
    global model
    try:
        model = joblib.load('models/weather_model.pkl')
        print("✅ 모델 로드 성공!")
    except:
        print("❌ 모델 파일이 없습니다. 먼저 학습을 실행하세요.")
        model = None

# 앱 시작시 모델 로드
load_model()

@app.get("/")
def root():
    return {"message": "Weather ML API 실행 중!", "model_loaded": model is not None}

@app.get("/health")
def health():
    return {"status": "healthy", "model_status": "loaded" if model else "not_loaded"}

@app.post("/predict")
def predict(humidity: float, pressure: float):
    if model is None:
        return {"error": "모델이 로드되지 않았습니다"}
    
    # 예측 수행
    prediction = model.predict([[humidity, pressure]])[0]
    
    return {
        "predicted_temperature": round(prediction, 2),
        "input": {"humidity": humidity, "pressure": pressure}
    }

@app.get("/predict/example")
def predict_example():
    """예시 예측"""
    if model is None:
        return {"error": "모델이 로드되지 않았습니다"}
    
    # 예시 데이터로 예측
    humidity, pressure = 65.0, 1013.2
    prediction = model.predict([[humidity, pressure]])[0]
    
    return {
        "predicted_temperature": round(prediction, 2),
        "input": {"humidity": humidity, "pressure": pressure},
        "note": "예시 예측 결과입니다"
>>>>>>> origin/main2
    }

if __name__ == "__main__":
    import uvicorn
<<<<<<< HEAD
    uvicorn.run(app, host="0.0.0.0", port=8000) 
=======
    uvicorn.run(app, host="0.0.0.0", port=8000)


>>>>>>> origin/main2
