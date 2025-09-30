import os
import sys
sys.path.append('/app')

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import pytz
import pandas as pd
import tempfile

# batch_predict.py에서 예측 함수 import
from src.models.batch_predict import batch_predict

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
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
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
    """쾌적지수 예측 (batch_predict.py 사용)"""
    if prediction_type not in ["now", "morning", "evening"]:
        raise HTTPException(status_code=400, detail="prediction_type은 now, morning, evening 중 하나여야 합니다")
    
    try:
        # 기본 날씨 데이터 (실제로는 실시간 데이터가 들어올 예정)
        weather_data = {
            'temperature': 20.0,
            'humidity': 60.0,
            'pressure': 1013.0,
            'wind_speed': 3.0,
            'wind_direction': 180.0,
            'dew_point': 15.0,
            'cloud_amount': 5.0,
            'visibility': 10000.0,
            'precipitation': 0.0,
            'sunshine': 5.0,
            'pm10': 30.0,
            'pm10_grade': 'good',
            'region': 'central',
            'datetime': datetime.now(),
            'station_id': '108'
        }
        
        # DataFrame으로 변환
        df = pd.DataFrame([weather_data])
        
        # 임시 CSV 파일 생성
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            temp_csv_path = f.name
        
        try:
            # batch_predict 함수 호출
            result_df = batch_predict(input_path=temp_csv_path)
            
            # 예측 결과 추출
            comfort_score = result_df['predicted_comfort_score'].iloc[0]
            
            # 시간대별 제목과 메시지
            titles = {
                "now": "📱 현재 시점 예측",
                "morning": "🌅 출근길 예측 (6-9시)", 
                "evening": "🌆 퇴근길 예측 (18-21시)"
            }
            
            # 점수에 따른 등급
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
                "prediction_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "weather_data": weather_data,
                "prediction_type": prediction_type,
                "status": "success"
            }
            
        finally:
            # 임시 파일 삭제
            os.unlink(temp_csv_path)
        
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