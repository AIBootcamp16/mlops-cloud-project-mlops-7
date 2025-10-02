import os
import sys
sys.path.append('/app')

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import pytz

from src.utils.mysql_utils import query_prediction_by_datetime
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Weather Comfort Score API", 
    version="0.1.0",
    description="batch_predict.py 기반 쾌적지수 예측 API"
)

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
    """쾌적지수 예측 (시간대 제한 포함)"""
    if prediction_type not in ["now", "morning", "evening"]:
        raise HTTPException(status_code=400, detail="prediction_type은 now, morning, evening 중 하나여야 합니다")
    
    try:
        kst = pytz.timezone('Asia/Seoul')
        current_time = datetime.now(kst)
        current_hour = current_time.hour
        
        # 시간대 제한 체크
        if prediction_type == "morning" and not (6 <= current_hour < 9):
            raise HTTPException(
                status_code=400,
                detail="출근길 쾌적지수는 오전 6시부터 9시 사이에만 볼 수 있어요."
            )
        
        if prediction_type == "evening" and not (14 <= current_hour < 22):
            raise HTTPException( 
                status_code=400,
                detail="퇴근길 쾌적지수는 오후 5시부터 10시 사이에만 볼 수 있어요."
            )
        
        # 현재 시간 데이터 조회
        current_hour_dt = current_time.replace(minute=0, second=0, microsecond=0)
        data = query_prediction_by_datetime(current_hour_dt)
        
        if not data:
            raise HTTPException(
                status_code=404, 
                detail=f"예측 데이터가 준비되지 않았습니다. (시간: {current_hour_dt})"
            )
        
        print(f"✅ DB 조회 성공: {current_hour_dt}")
        comfort_score = data['comfort_score']
        weather_data = {
            'temperature': data.get('temperature'),
            'humidity': data.get('humidity'),
            'rainfall': data.get('rainfall'),
            'pm10': data.get('pm10'),
            'wind_speed': data.get('wind_speed'),
            'pressure': data.get('pressure'),
            'region': data.get('region'),
            'station_id': data.get('station_id')
        }
        
        titles = {
            "now": "📱 현재 시점",
            "morning": "🌅 출근길 예측 (6-9시)", 
            "evening": "🌆 퇴근길 예측 (17-22시)"
        }
        
        if comfort_score >= 80:
            label = "excellent"
            evaluation = "최고로 쾌적합니다! 🌟"
        elif comfort_score >= 60:
            label = "good"
            evaluation = "쾌적합니다 😊"
        elif comfort_score >= 40:
            label = "moderate"
            evaluation = "보통입니다 😐"
        elif comfort_score >= 20:
            label = "poor"
            evaluation = "다소 불쾌합니다 😟"
        else:
            label = "very_poor"
            evaluation = "불쾌합니다 ⚠️"
        
        return {
            "title": titles[prediction_type],
            "score": round(comfort_score, 1),
            "label": label,
            "evaluation": evaluation,
            "prediction_time": current_hour_dt.strftime("%Y-%m-%d %H:%M"),
            "weather_data": weather_data,
            "prediction_type": prediction_type,
            "status": "success"
        }
        
    except HTTPException:
        raise
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
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)