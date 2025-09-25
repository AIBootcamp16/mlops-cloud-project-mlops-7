#!/usr/bin/env python3
"""
MLOps 기상 데이터 예측 서비스 Fast API 서버

모델링팀의 모델 개발과 병렬로 개발되는 API 서버
Mock 모델을 사용하여 인터페이스를 먼저 구축하고, 실제 모델로 교체 가능하도록 설계
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path
import traceback
import asyncio
import logging

# 프로젝트 루트를 path에 추가
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))

from src.features.feature_builder import create_ml_dataset
from src.utils.logger_config import get_logger

# 로거 설정
logger = get_logger(__name__)

# 전역 변수
model_manager = None
data_processor = None

class WeatherRequest(BaseModel):
    """기상 예측 요청 모델"""
    station_ids: Optional[List[str]] = Field(default=None, description="관측소 ID 목록 (None이면 전체)")
    datetime: Optional[str] = Field(default=None, description="예측 시간 (ISO format, None이면 현재 시간)")
    features: Optional[Dict[str, Any]] = Field(default=None, description="추가 피처 데이터")

    class Config:
        schema_extra = {
            "example": {
                "station_ids": ["108", "112", "119"],
                "datetime": "2025-09-25T14:00:00Z",
                "features": {
                    "temperature": 25.5,
                    "humidity": 60.0,
                    "pressure": 1013.2
                }
            }
        }

class WeatherResponse(BaseModel):
    """기상 예측 응답 모델"""
    predictions: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    processing_time: float

    class Config:
        schema_extra = {
            "example": {
                "predictions": [
                    {
                        "station_id": "108",
                        "datetime": "2025-09-25T14:00:00Z",
                        "predicted_temperature": 25.3,
                        "predicted_pm10": 12.5,
                        "comfort_score": 85.2,
                        "confidence": 0.92
                    }
                ],
                "metadata": {
                    "model_version": "v1.0.0",
                    "feature_count": 30,
                    "stations_count": 23
                },
                "processing_time": 0.15
            }
        }

class HealthResponse(BaseModel):
    """헬스 체크 응답 모델"""
    status: str
    timestamp: str
    service: str
    version: str
    model_loaded: bool
    data_processor_loaded: bool

class ModelManager:
    """모델 로딩 및 관리 클래스"""

    def __init__(self):
        self.model = None
        self.model_metadata = {
            "version": "v1.0.0-mock",
            "type": "ensemble",
            "trained_date": "2025-09-25",
            "feature_count": 30
        }
        self.is_loaded = False

    async def load_model(self):
        """모델 로딩 (현재는 Mock 모델)"""
        try:
            logger.info("모델 로딩 시작...")

            # 실제 모델이 준비되면 여기서 로드
            # import joblib
            # self.model = joblib.load("models/weather_prediction_model.pkl")

            # 현재는 Mock 모델 사용
            await asyncio.sleep(1)  # 모델 로딩 시뮬레이션
            self.model = MockWeatherModel()

            self.is_loaded = True
            logger.info(f"모델 로딩 완료: {self.model_metadata}")

        except Exception as e:
            logger.error(f"모델 로딩 실패: {e}")
            self.is_loaded = False
            raise

    async def predict(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """예측 수행"""
        if not self.is_loaded or self.model is None:
            raise HTTPException(status_code=503, detail="Model not loaded")

        try:
            # 실제 모델 예측
            predictions = await self.model.predict(features_df)
            return predictions

        except Exception as e:
            logger.error(f"예측 실패: {e}")
            raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

class MockWeatherModel:
    """실제 모델 대신 사용할 Mock 모델"""

    async def predict(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """Mock 예측 (실제 모델과 동일한 인터페이스)"""

        predictions = []

        for _, row in features_df.iterrows():
            # Mock 예측값 생성 (실제 피처 기반)
            base_temp = row.get('temperature', 20.0)
            base_pm10 = row.get('pm10', 15.0)

            prediction = {
                'station_id': row.get('station_id', 'unknown'),
                'datetime': row.get('datetime', datetime.now().isoformat()),
                'predicted_temperature': base_temp + np.random.normal(0, 1),
                'predicted_pm10': max(0, base_pm10 + np.random.normal(0, 3)),
                'comfort_score': row.get('comfort_score', 75.0) + np.random.normal(0, 5),
                'confidence': np.random.uniform(0.85, 0.95)
            }
            predictions.append(prediction)

        return pd.DataFrame(predictions)

class DataProcessor:
    """데이터 전처리 파이프라인"""

    def __init__(self):
        self.is_loaded = False
        self.feature_columns = []

    async def load_processor(self):
        """전처리 파이프라인 로딩"""
        try:
            logger.info("데이터 전처리 파이프라인 로딩 중...")

            # 피처 컬럼 목록 정의 (실제 ML 데이터셋과 동일)
            self.feature_columns = [
                'station_id', 'datetime', 'temperature', 'pm10',
                'hour', 'day_of_week', 'month', 'season',
                'is_rush_hour', 'is_morning_rush', 'is_evening_rush',
                'is_weekday', 'is_weekend', 'temp_category', 'temp_comfort',
                'temp_extreme', 'heating_needed', 'cooling_needed',
                'is_metro_area', 'is_coastal', 'region',
                'pm10_grade', 'mask_needed', 'outdoor_activity_ok',
                'comfort_score'
            ]

            self.is_loaded = True
            logger.info("데이터 전처리 파이프라인 로딩 완료")

        except Exception as e:
            logger.error(f"데이터 전처리 파이프라인 로딩 실패: {e}")
            self.is_loaded = False
            raise

    async def prepare_features(self, request_data: WeatherRequest) -> pd.DataFrame:
        """요청 데이터를 ML 피처로 변환"""
        try:
            # 현재 시간 설정
            if request_data.datetime:
                current_time = datetime.fromisoformat(request_data.datetime.replace('Z', '+00:00'))
            else:
                current_time = datetime.now()

            # 기본 raw_data 구조 생성
            raw_data = {
                "asos": [],
                "pm10": [],
                "uv": []
            }

            # 관측소 목록 설정
            station_ids = request_data.station_ids or ["108", "112", "119", "133"]  # 기본 주요 관측소

            observed_at = current_time.isoformat() + "Z"

            # 요청 데이터나 기본값으로 raw_data 구성
            for station_id in station_ids:
                # ASOS 데이터
                temp_value = None
                if request_data.features:
                    temp_value = request_data.features.get('temperature')

                if temp_value is None:
                    temp_value = np.random.normal(20, 10)  # Mock 온도

                raw_data["asos"].append({
                    "station_id": station_id,
                    "observed_at": observed_at,
                    "value": temp_value
                })

                # PM10 데이터
                pm10_value = None
                if request_data.features:
                    pm10_value = request_data.features.get('pm10')

                if pm10_value is None:
                    pm10_value = np.random.uniform(5, 30)  # Mock PM10

                raw_data["pm10"].append({
                    "station_id": station_id,
                    "observed_at": observed_at,
                    "value": pm10_value
                })

            # 기존 feature_builder 사용하여 ML 피처 생성
            ml_features = create_ml_dataset(raw_data)

            logger.info(f"피처 생성 완료: {ml_features.shape}")
            return ml_features

        except Exception as e:
            logger.error(f"피처 생성 실패: {e}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Feature preparation failed: {str(e)}")

async def get_model_manager():
    """모델 매니저 의존성 주입"""
    global model_manager
    if model_manager is None or not model_manager.is_loaded:
        raise HTTPException(status_code=503, detail="Model not available")
    return model_manager

async def get_data_processor():
    """데이터 프로세서 의존성 주입"""
    global data_processor
    if data_processor is None or not data_processor.is_loaded:
        raise HTTPException(status_code=503, detail="Data processor not available")
    return data_processor

@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 생명주기 관리"""
    global model_manager, data_processor

    # 시작 시
    logger.info("=== MLOps 기상 예측 서비스 시작 ===")

    try:
        # 모델 매니저 초기화
        model_manager = ModelManager()
        await model_manager.load_model()

        # 데이터 프로세서 초기화
        data_processor = DataProcessor()
        await data_processor.load_processor()

        logger.info("서비스 초기화 완료")

    except Exception as e:
        logger.error(f"서비스 초기화 실패: {e}")
        # 초기화 실패해도 서비스는 시작 (헬스체크에서 확인 가능)

    yield

    # 종료 시
    logger.info("=== MLOps 기상 예측 서비스 종료 ===")

# FastAPI 앱 생성
app = FastAPI(
    title="MLOps 기상 데이터 예측 API",
    description="기상청 데이터 기반 기상 예측 및 쾌적지수 계산 서비스",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 미들웨어
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경용, 프로덕션에서는 제한 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/", response_model=Dict[str, str])
async def root():
    """루트 엔드포인트"""
    return {
        "service": "MLOps 기상 예측 API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스 체크 엔드포인트"""
    global model_manager, data_processor

    return HealthResponse(
        status="healthy" if (model_manager and model_manager.is_loaded and
                           data_processor and data_processor.is_loaded) else "degraded",
        timestamp=datetime.now().isoformat(),
        service="weather-prediction-api",
        version="1.0.0",
        model_loaded=model_manager.is_loaded if model_manager else False,
        data_processor_loaded=data_processor.is_loaded if data_processor else False
    )

@app.post("/predict", response_model=WeatherResponse)
async def predict_weather(
    request: WeatherRequest,
    model_mgr: ModelManager = Depends(get_model_manager),
    processor: DataProcessor = Depends(get_data_processor)
):
    """기상 데이터 예측"""
    start_time = datetime.now()

    try:
        logger.info(f"예측 요청: {request.dict()}")

        # 1. 피처 준비
        features_df = await processor.prepare_features(request)

        # 2. 예측 수행
        predictions_df = await model_mgr.predict(features_df)

        # 3. 응답 데이터 구성
        predictions = predictions_df.to_dict('records')

        processing_time = (datetime.now() - start_time).total_seconds()

        response = WeatherResponse(
            predictions=predictions,
            metadata={
                "model_version": model_mgr.model_metadata["version"],
                "feature_count": len(features_df.columns) if not features_df.empty else 0,
                "stations_count": len(predictions),
                "request_time": start_time.isoformat(),
                "processing_time": processing_time
            },
            processing_time=processing_time
        )

        logger.info(f"예측 완료: {len(predictions)}개 관측소, {processing_time:.3f}초")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"예측 처리 중 오류: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stations")
async def get_available_stations():
    """사용 가능한 관측소 목록"""
    # 실제로는 DB나 설정에서 가져올 수 있음
    stations = [
        {"id": "100", "name": "속초", "region": "강원", "lat": 38.25, "lon": 128.56},
        {"id": "101", "name": "북춘천", "region": "강원", "lat": 37.87, "lon": 127.73},
        {"id": "108", "name": "서울", "region": "경기", "lat": 37.57, "lon": 126.97},
        {"id": "112", "name": "인천", "region": "경기", "lat": 37.48, "lon": 126.62},
        {"id": "119", "name": "수원", "region": "경기", "lat": 37.29, "lon": 127.01},
        {"id": "133", "name": "대전", "region": "충남", "lat": 36.37, "lon": 127.37}
    ]

    return {
        "stations": stations,
        "total_count": len(stations),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/model/info")
async def get_model_info(model_mgr: ModelManager = Depends(get_model_manager)):
    """모델 정보"""
    return {
        "model_metadata": model_mgr.model_metadata,
        "is_loaded": model_mgr.is_loaded,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/reload")
async def reload_services(background_tasks: BackgroundTasks):
    """서비스 재로딩 (개발 환경용)"""
    async def reload_task():
        global model_manager, data_processor
        try:
            logger.info("서비스 재로딩 시작")

            if model_manager:
                await model_manager.load_model()

            if data_processor:
                await data_processor.load_processor()

            logger.info("서비스 재로딩 완료")
        except Exception as e:
            logger.error(f"서비스 재로딩 실패: {e}")

    background_tasks.add_task(reload_task)
    return {"message": "Reload initiated", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn

    # 개발 서버 실행
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )