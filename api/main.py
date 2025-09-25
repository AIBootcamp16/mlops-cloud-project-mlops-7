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
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


