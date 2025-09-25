#!/usr/bin/env python3
"""
간단한 MLOps 기상 데이터 예측 API 서버
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))

from src.features.feature_builder import create_ml_dataset
# import joblib  # 실제 모델 사용 시 주석 해제

# FastAPI 앱 생성
app = FastAPI(
    title="출퇴근길 쾌적지수 예측모델",
    version="1.0.0"
)

class WeatherRequest(BaseModel):
    station_ids: Optional[List[str]] = None
    datetime: Optional[str] = None
    features: Optional[Dict[str, Any]] = None

class WeatherResponse(BaseModel):
    predictions: List[Dict[str, Any]]
    processing_time: float

@app.get("/")
async def root():
    return {
        "service": "출퇴근길 쾌적지수 예측모델",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/predict", response_model=WeatherResponse)
async def predict(request: WeatherRequest):
    start_time = datetime.now()

    # 기본값 설정
    station_ids = request.station_ids or ["108", "112", "119"]
    current_time = datetime.now()
    if request.datetime:
        current_time = datetime.fromisoformat(request.datetime.replace('Z', '+00:00'))

    # Mock 데이터 생성
    raw_data = {"asos": [], "pm10": []}
    observed_at = current_time.isoformat() + "Z"

    for station_id in station_ids:
        # 기본 온도와 PM10 값
        temp = 20 + np.random.normal(0, 5)
        pm10 = 15 + np.random.uniform(0, 10)

        # 요청에서 값이 있으면 사용
        if request.features:
            temp = request.features.get('temperature', temp)
            pm10 = request.features.get('pm10', pm10)

        raw_data["asos"].append({
            "station_id": station_id,
            "observed_at": observed_at,
            "value": temp
        })
        raw_data["pm10"].append({
            "station_id": station_id,
            "observed_at": observed_at,
            "value": pm10
        })

    # ML 피처 생성
    ml_features = create_ml_dataset(raw_data)

    # Mock 예측 (실제 모델로 교체 시 이 부분만 수정)
    predictions = []
    for _, row in ml_features.iterrows():
        predictions.append({
            "station_id": row.get('station_id', 'unknown'),
            "datetime": row.get('datetime', current_time.isoformat()),
            "predicted_temperature": row.get('temperature', 20) + np.random.normal(0, 1),
            "predicted_pm10": max(0, row.get('pm10', 15) + np.random.normal(0, 2)),
            "comfort_score": row.get('comfort_score', 75) + np.random.normal(0, 3),
            "confidence": np.random.uniform(0.85, 0.95)
        })

    # 실제 모델 사용 시:
    # model = joblib.load("models/weather_model.pkl")
    # predictions = model.predict(ml_features).to_dict('records')

    processing_time = (datetime.now() - start_time).total_seconds()

    return WeatherResponse(
        predictions=predictions,
        processing_time=processing_time
    )

@app.get("/stations")
async def get_stations():
    stations = [
        {"id": "108", "name": "서울"},
        {"id": "112", "name": "인천"},
        {"id": "119", "name": "수원"},
        {"id": "133", "name": "대전"}
    ]
    return {"stations": stations, "count": len(stations)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)