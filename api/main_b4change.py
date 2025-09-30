import os
import sys
sys.path.append('/app')

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import pandas as pd
import numpy as np
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import pytz
import requests
import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from src.utils.utils import get_s3_client
from src.data.data_cleaning import (
    add_time_features,
    add_temp_features,
    add_air_quality_features,
    add_region_features
)
import boto3
import pickle
from io import BytesIO
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 전역 변수
model = None
scaler = None

# 캐시 시스템
weather_cache = {
    "now": {"data": None, "timestamp": None, "last_update": None},
    "morning": {"data": None, "timestamp": None, "last_update": None},
    "evening": {"data": None, "timestamp": None, "last_update": None}
}

# 캐시 설정
CACHE_DURATION_MINUTES = 10  # 10분 캐시 유지
UPDATE_INTERVAL_MINUTES = 5   # 5분마다 백그라운드 업데이트
cache_lock = threading.Lock()
background_task_running = False

# 기상청 API 설정 (좌표 기반)
def get_kma_real_weather(lat=37.5665, lon=126.9780):
    """좌표 기반 실시간 날씨 데이터 (기본값: 서울)"""
    try:
        # 기상청 API 설정
        auth_key = os.getenv("WEATHER_API_KEY")
        
        if not auth_key:
            print("⚠️ WEATHER_API_KEY가 설정되지 않음. 모킹 데이터 사용")
            return None
            

        
        # 기상청 API Hub (팀원이 사용했던 URL)
        base_url = "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm2.php"
        
        params = {
            'authKey': auth_key,
            'stn': '108',  # 서울 관측소 (기본값)
            'schListCnt': 1,  # 최신 1개 데이터만
            'disp': 1         # JSON 형태
        }
        
        print(f"🌐 기상청 API 호출: {base_url}")
        print(f"📍 관측소: 108 (서울)")
        
        response = requests.get(base_url, params=params, timeout=10)
        
        print(f"📡 API 응답: {response.status_code}")
        
        if response.status_code == 200:
            text_data = response.text
            print(f"📊 응답 데이터: 텍스트 형식, 길이: {len(text_data)}")
            
            # KMA API Hub 텍스트 응답 파싱
            lines = text_data.strip().split('\n')
            data_line = None
            
            # 데이터 라인 찾기 (숫자로 시작하는 라인)
            for line in lines:
                if line.strip() and line.strip()[0].isdigit():
                    data_line = line.strip()
                    break
            
            if data_line:
                # 고정폭 텍스트 파싱
                parts = data_line.split()
                print(f"🌤️ 파싱된 데이터: {len(parts)}개 항목")
                
                if len(parts) >= 20:  # 충분한 데이터가 있는지 확인
                    try:
                        # 올바른 인덱스로 수정 (스페이스 기준 파싱)
                        def safe_float(value, default=None):
                            """안전한 float 변환 (-9, -, 빈값 처리)"""
                            if value in ['-9', '-', '', 'None']:
                                return default
                            try:
                                return float(value)
                            except (ValueError, TypeError):
                                return default
                        
                        return {
                            "timestamp": datetime.now(),
                            "temperature": safe_float(parts[11]),    # TA (기온) - 11번째
                            "humidity": safe_float(parts[13]),       # HM (습도) - 13번째  
                            "pressure": safe_float(parts[7]),        # PS (해면기압) - 7번째
                            "wind_speed": safe_float(parts[3]),      # WS (풍속) - 3번째
                            "wind_direction": safe_float(parts[2]),  # WD (풍향) - 2번째
                            "precipitation": safe_float(parts[14], 0.0), # RN (강수량) - 14번째
                            "visibility": safe_float(parts[-8]) if len(parts) > 35 else None,  # VS (가시거리)
                            "cloud_amount": safe_float(parts[-18]) if len(parts) > 35 else None, # CA (운량)
                            "dew_point": safe_float(parts[12]),     # TD (이슬점) - 12번째
                        }
                    except (ValueError, IndexError) as e:
                        print(f"⚠️ 데이터 파싱 오류: {e}")
                        print(f"📋 원본 데이터: {data_line}")
                        return None
                else:
                    print(f"⚠️ 데이터 항목 부족: {len(parts)}개")
            else:
                print("⚠️ 유효한 데이터 라인을 찾을 수 없음")
        
        print(f"⚠️ 기상청 API 응답 오류: {response.status_code}")
        if response.status_code != 200:
            print(f"📄 응답 내용: {response.text[:500]}")
        return None
        
    except Exception as e:
        print(f"⚠️ 기상청 API 호출 실패: {e}")
        import traceback
        traceback.print_exc()
        return None



# PM10 (미세먼지) API 연동
def get_pm10_data():
    """실시간 PM10 (미세먼지) 데이터 수집"""
    try:
        auth_key = os.getenv("WEATHER_API_KEY")
        
        if not auth_key:
            print("⚠️ WEATHER_API_KEY가 설정되지 않음")
            return None
        
        base_url = "https://apihub.kma.go.kr/api/typ01/url/kma_pm10.php"
        
        # 현재 시간 기준 1시간 전부터 현재까지
        current_time = datetime.now()
        start_time = current_time - timedelta(hours=1)
        
        params = {
            'tm1': start_time.strftime('%Y%m%d%H%M'),
            'tm2': current_time.strftime('%Y%m%d%H%M'),
            'stn': 108,  # 서울 관측소
            'authKey': auth_key
        }
        
        print(f"🌫️ PM10 API 호출: {base_url}")
        print(f"📍 관측소: 108 (서울), 시간: {start_time.strftime('%Y%m%d%H%M')} - {current_time.strftime('%Y%m%d%H%M')}")
        
        response = requests.get(base_url, params=params, timeout=10)
        print(f"📡 PM10 API 응답: {response.status_code}")
        
        if response.status_code == 200:
            text_data = response.text
            print(f"📊 PM10 응답 데이터: 텍스트 형식, 길이: {len(text_data)}")
            
            lines = text_data.strip().split('\n')
            pm10_value = None
            
            # 가장 최근 유효한 PM10 데이터 찾기
            for line in reversed(lines):
                if line.strip() and not line.startswith('#'):
                    parts = line.split(',')
                    if len(parts) >= 3:
                        try:
                            pm10_raw = parts[2].strip()
                            if pm10_raw not in ['-9', '-', '']:
                                pm10_value = float(pm10_raw)
                                break
                        except (ValueError, IndexError):
                            continue
            
            if pm10_value is not None:
                # PM10 등급 결정
                if pm10_value <= 30:
                    pm10_grade = "좋음"
                elif pm10_value <= 80:
                    pm10_grade = "보통"
                elif pm10_value <= 150:
                    pm10_grade = "나쁨"
                else:
                    pm10_grade = "매우나쁨"
                
                print(f"🌫️ PM10 데이터: {pm10_value}㎍/㎥ ({pm10_grade})")
                return {
                    "pm10": pm10_value,
                    "pm10_grade": pm10_grade
                }
            else:
                print("⚠️ 유효한 PM10 데이터를 찾을 수 없음")
                return {
                    "pm10": 30.0,  # 기본값
                    "pm10_grade": "좋음"
                }
        else:
            print(f"⚠️ PM10 API 응답 오류: {response.status_code}")
            return {
                "pm10": 30.0,  # 기본값
                "pm10_grade": "좋음"
            }
            
    except Exception as e:
        print(f"⚠️ PM10 API 호출 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


# 기상청 단기예보 API 연동
def get_kma_forecast_weather(target_date=None, target_hour=None):
    """기상청 API Hub 단기예보 API를 사용한 진짜 미래 날씨 예측"""
    try:
        auth_key = os.getenv("WEATHER_API_KEY")
        
        if not auth_key:
            print("⚠️ WEATHER_API_KEY가 설정되지 않음")
            return None
        
        kst = pytz.timezone('Asia/Seoul')
        current_time = datetime.now(kst)
        
        # 기본값 설정
        if target_date is None:
            target_date = current_time.date()
        if target_hour is None:
            target_hour = current_time.hour
            
        target_datetime = datetime.combine(target_date, datetime.min.time().replace(hour=target_hour))
        
        print(f"🔮 기상청 API Hub 단기예보 API 호출")
        print(f"📍 목표 시간: {target_datetime.strftime('%Y-%m-%d %H:00')}")
        
        # 기상청 API Hub 단기예보 격자자료 API 사용
        base_url = "https://apihub.kma.go.kr/api/typ01/cgi-bin/url/nph-dfs_shrt_grd"
        
        # 현재 시간 기준 가장 최근 발표시간 계산
        current_hour = current_time.hour
        if current_hour < 2:
            forecast_hour = "23"
            forecast_date = (current_time - timedelta(days=1)).strftime("%Y%m%d")
        elif current_hour < 5:
            forecast_hour = "02"
            forecast_date = current_time.strftime("%Y%m%d")
        elif current_hour < 8:
            forecast_hour = "05"
            forecast_date = current_time.strftime("%Y%m%d")
        elif current_hour < 11:
            forecast_hour = "08"
            forecast_date = current_time.strftime("%Y%m%d")
        elif current_hour < 14:
            forecast_hour = "11"
            forecast_date = current_time.strftime("%Y%m%d")
        elif current_hour < 17:
            forecast_hour = "14"
            forecast_date = current_time.strftime("%Y%m%d")
        elif current_hour < 20:
            forecast_hour = "17"
            forecast_date = current_time.strftime("%Y%m%d")
        else:
            forecast_hour = "20"
            forecast_date = current_time.strftime("%Y%m%d")
        
        tmfc = forecast_date + forecast_hour  # 발표시간
        tmef = target_datetime.strftime("%Y%m%d%H")  # 발효시간 (예측하고자 하는 시간)
        
        params = {
            'tmfc': tmfc,  # 발표시간
            'tmef': tmef,  # 발효시간
            'vars': 'TMP,REH,PRS,WSD,VEC,PCP,SKY,PTY',  # 기온,습도,기압,풍속,풍향,강수량,하늘상태,강수형태
            'x': 60,       # 서울 격자 X좌표
            'y': 127,      # 서울 격자 Y좌표
            'authKey': auth_key
        }
        
        print(f"🌐 단기예보 격자자료 API 호출: {base_url}")
        print(f"📍 격자좌표: (60, 127) 서울")
        print(f"📅 발표시간: {tmfc}, 발효시간: {tmef}")
        
        response = requests.get(base_url, params=params, timeout=10)
        print(f"📡 단기예보 API 응답: {response.status_code}")
        
        if response.status_code == 200:
            try:
                # 격자자료 API 응답 파싱
                text_data = response.text.strip()
                print(f"📊 단기예보 응답 데이터: 텍스트 형식, 길이: {len(text_data)}")
                
                if text_data and not text_data.startswith('<!DOCTYPE') and not text_data.startswith('{'):
                    # 공백으로 구분된 데이터 파싱
                    values = text_data.split()
                    print(f"🔍 파싱된 값들: {values[:10]}...")  # 처음 10개 값만 로그
                    
                    if len(values) >= 8:  # 최소 8개 변수 (TMP,REH,PRS,WSD,VEC,PCP,SKY,PTY)
                        try:
                            def safe_float(value, default=None):
                                """안전한 float 변환"""
                                if value in ['-9', '-', '', 'None', 'nan']:
                                    return default
                                try:
                                    return float(value)
                                except (ValueError, TypeError):
                                    return default
                            
                            # 격자자료 API 응답 순서: TMP,REH,PRS,WSD,VEC,PCP,SKY,PTY
                            temperature = safe_float(values[0], 20.0)      # TMP: 기온
                            humidity = safe_float(values[1], 60.0)         # REH: 습도
                            pressure = safe_float(values[2], 1013.0)       # PRS: 기압 (hPa)
                            wind_speed = safe_float(values[3], 3.0)        # WSD: 풍속
                            wind_direction = safe_float(values[4], 180.0)  # VEC: 풍향
                            precipitation = safe_float(values[5], 0.0)     # PCP: 강수량
                            sky_state = safe_float(values[6], 3.0)         # SKY: 하늘상태 (1:맑음, 3:구름많음, 4:흐림)
                            precip_type = safe_float(values[7], 0.0)       # PTY: 강수형태 (0:없음, 1:비, 2:비/눈, 3:눈)
                            
                            forecast_data = {
                                'timestamp': target_datetime,
                                'temperature': temperature,
                                'humidity': humidity,
                                'pressure': pressure,
                                'wind_speed': wind_speed,
                                'wind_direction': wind_direction,
                                'precipitation': precipitation,
                                'visibility': 10000.0,  # 격자자료에 없으므로 기본값
                                'cloud_amount': sky_state,  # 하늘상태를 운량으로 사용
                                'dew_point': temperature - ((100 - humidity) / 5) if humidity else 15.0,  # 이슬점 추정
                            }
                            
                            print(f"✅ 단기예보 격자자료 파싱 성공")
                            print(f"🌡️ 예보 기온: {temperature}°C, 습도: {humidity}%, 강수: {precipitation}mm")
                            return forecast_data
                            
                        except (ValueError, IndexError) as e:
                            print(f"⚠️ 데이터 파싱 중 오류: {e}")
                    else:
                        print(f"⚠️ 데이터 부족: {len(values)}개 값")
                else:
                    print(f"⚠️ 예상치 못한 응답 형식: {text_data[:100]}...")
                                
            except Exception as e:
                print(f"⚠️ 단기예보 데이터 파싱 실패: {e}")
        
        print(f"❌ 단기예보 API 호출 실패 또는 파싱 실패: {response.status_code}")
        if response.status_code != 200:
            print(f"📄 응답 내용: {response.text[:200]}")
        
        # 실패 시 실시간 데이터로 대체
        print("⚠️ 단기예보 실패, 실시간 데이터로 대체")
        real_weather = get_kma_real_weather()
        
        if real_weather:
            forecast_data = {
                'timestamp': target_datetime,
                'temperature': real_weather.get('temperature', 20.0),
                'humidity': real_weather.get('humidity', 60.0),
                'pressure': real_weather.get('pressure', 1013.0),
                'wind_speed': real_weather.get('wind_speed', 3.0),
                'wind_direction': real_weather.get('wind_direction', 180.0),
                'precipitation': real_weather.get('precipitation', 0.0),
                'visibility': real_weather.get('visibility', 10000.0),
                'cloud_amount': real_weather.get('cloud_amount', 3.0),
                'dew_point': real_weather.get('dew_point', 15.0),
            }
            print(f"✅ 실시간 데이터로 대체 완료")
            return forecast_data
        
        return None
        
    except Exception as e:
        print(f"⚠️ 단기예보 API 호출 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_forecast_weather_with_pm10(target_date=None, target_hour=None):
    """단기예보 + PM10 데이터 통합"""
    # 1단계: 단기예보 데이터
    forecast_data = get_kma_forecast_weather(target_date, target_hour)
    
    if not forecast_data:
        print("❌ 단기예보 데이터를 가져올 수 없습니다")
        return None
    
    # 2단계: PM10 데이터 추가 (현재 데이터 사용, 미래 PM10 예보는 별도 API 필요)
    pm10_data = get_pm10_data()
    if pm10_data:
        forecast_data.update(pm10_data)
    else:
        # 기본 PM10 데이터
        forecast_data.update({
            "pm10": 30.0,
            "pm10_grade": "좋음"
        })
    
    # 3단계: 지역 정보 추가
    forecast_data["region"] = "서울특별시"
    
    print(f"✅ 단기예보 + PM10 데이터 통합 완료")
    return forecast_data


def get_current_weather_real(lat=37.5665, lon=126.9780):
    """실제 기상청 API + PM10 API + 폴백 시스템 (좌표 기반)"""
    # 1단계: 실제 기상청 API 시도
    real_data = get_kma_real_weather(lat, lon)
    
    # 2단계: PM10 데이터 추가
    pm10_data = get_pm10_data()
    
    if real_data:
        print(f"✅ 실제 기상청 데이터 사용 (위도:{lat}, 경도:{lon})")
        # PM10 데이터 병합
        real_data.update(pm10_data)
        # region 필드 추가 (서울 기본값)
        real_data["region"] = "서울특별시"
        return real_data
    
    # 실시간 데이터를 가져올 수 없는 경우
    print("❌ 실시간 데이터를 가져올 수 없습니다")
    return None

class WeatherInput(BaseModel):
    """날씨 입력 데이터 모델 (app.py와 동일한 구조)"""
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    pressure: Optional[float] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[float] = None
    dew_point: Optional[float] = None
    cloud_amount: Optional[float] = None
    visibility: Optional[float] = None
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
    """data_cleaning.py와 동일한 전처리 파이프라인 사용"""
    # WeatherInput을 딕셔너리로 변환하고 None 값 처리
    input_dict = data.dict()
    
    # None 값을 기본값으로 대체
    defaults = {
        'temperature': 20.0,
        'humidity': 60.0,
        'pressure': 1013.0,
        'wind_speed': 3.0,
        'wind_direction': 180.0,
        'dew_point': 15.0,
        'cloud_amount': 5.0,
        'visibility': 10000.0
    }
    
    for key, default_value in defaults.items():
        if input_dict.get(key) is None:
            input_dict[key] = default_value
    
    # DataFrame 생성 (data_cleaning.py 형식에 맞춤)
    df = pd.DataFrame([input_dict])
    
    # 필수 컬럼들 추가 (data_cleaning.py에서 필요한 형식)
    df['station_id'] = '108'  # 서울 관측소
    df['datetime'] = pd.Timestamp.now()  # 현재 시간
    df['rainfall'] = -9.0  # 고결측 컬럼 (나중에 제거됨)
    df['sunshine'] = 5.0   # 기본값
    
    # PM10 등급을 영어로 변환 (data_cleaning.py는 영어 등급 사용)
    pm10_grade_map = {
        '좋음': 'good',
        '보통': 'moderate', 
        '나쁨': 'bad',
        '매우나쁨': 'very_bad'
    }
    df['pm10_grade'] = pm10_grade_map.get(data.pm10_grade, 'good')
    
    # 지역을 영어로 변환
    region_map = {
        '서울특별시': 'central',
        '부산광역시': 'southern',
        '대구광역시': 'southern'
    }
    df['region'] = region_map.get(data.region, 'central')
    
    print(f"🔧 data_cleaning.py 전처리 파이프라인 시작")
    
    # 1단계: data_cleaning.py의 시간 피처 추가
    df = add_time_features(df, dt_col='datetime')
    
    # 2단계: data_cleaning.py의 온도 피처 추가
    df = add_temp_features(df, temp_col='temperature')
    
    # 3단계: data_cleaning.py의 미세먼지 피처 추가 (PM10 값 추가 필요)
    df['pm10'] = 30.0  # 기본값 (add_air_quality_features에서 필요)
    df = add_air_quality_features(df, pm10_col='pm10')
    
    # 4단계: data_cleaning.py의 지역 피처 추가
    df = add_region_features(df, station_col='station_id')
    
    print(f"✅ data_cleaning.py 전처리 완료")
    
    # 5단계: split.py와 동일한 후처리
    # 타겟 컬럼 제외
    target_col = "comfort_score"
    exclude_cols = [target_col, "pm10", "datetime", "station_id"]
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    X = df[feature_cols].copy()
    
    # 결측치 처리 (-99, -9를 NaN으로 변환 후 평균값 대체)
    X = X.replace([-99, -9], np.nan)
    numeric_cols = X.select_dtypes(include=[np.number]).columns
    X[numeric_cols] = X[numeric_cols].fillna(X[numeric_cols].mean())
    
    # 고결측 컬럼 제거 (rainfall 제거)
    high_missing_cols = ['rainfall']
    X = X.drop(columns=[col for col in high_missing_cols if col in X.columns])
    
    # 범주형 변수 원핫인코딩
    categorical_cols = ['season', 'temp_category', 'pm10_grade', 'region']
    categorical_cols = [col for col in categorical_cols if col in X.columns]
    
    if categorical_cols:
        X = pd.get_dummies(X, columns=categorical_cols, drop_first=True)
    
    # 실제 학습 시 사용된 37개 피처
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
    
    print(f"🎯 최종 피처 수: {X.shape[1]}개")
    return X

def convert_score_to_10_scale(score_100):
    """100점 척도를 10점 척도로 변환 (노트북 데이터 범위: 4.5~91.5)"""
    # 실제 데이터 범위에 맞춰 정규화 후 10점 척도로 변환
    min_score, max_score = 4.5, 91.5
    normalized = (score_100 - min_score) / (max_score - min_score)
    return normalized * 10



def get_temp_category(temperature):
    """온도에 따른 자동 카테고리 분류"""
    if temperature < 0:
        return "very_cold"
    elif temperature < 10:
        return "cold"
    elif temperature < 20:
        return "mild"
    elif temperature < 30:
        return "warm"
    else:
        return "hot"

def get_current_season():
    """현재 계절 자동 판단"""
    month = datetime.now().month
    if month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    elif month in [9, 10, 11]:
        return "autumn"
    else:
        return "winter"

# 캐시 관련 함수들
def is_cache_valid(prediction_type: str) -> bool:
    """캐시가 유효한지 확인"""
    with cache_lock:
        cache_entry = weather_cache.get(prediction_type)
        if not cache_entry or not cache_entry["last_update"]:
            return False
        
        elapsed = datetime.now() - cache_entry["last_update"]
        return elapsed.total_seconds() < (CACHE_DURATION_MINUTES * 60)

def get_cached_prediction(prediction_type: str) -> Optional[Dict[Any, Any]]:
    """캐시된 예측 결과 가져오기"""
    with cache_lock:
        if is_cache_valid(prediction_type):
            cache_entry = weather_cache[prediction_type]
            # 조회 시각만 최신으로 업데이트
            if cache_entry["data"]:
                current_time = datetime.now(pytz.timezone('Asia/Seoul'))
                cache_entry["data"]["prediction_time"] = current_time.strftime("%Y-%m-%d %H:%M")
                print(f"📋 캐시에서 {prediction_type} 데이터 반환 (마지막 업데이트: {cache_entry['last_update']})")
                return cache_entry["data"].copy()
        return None

def update_cache(prediction_type: str, prediction_data: Dict[Any, Any]):
    """캐시 업데이트"""
    with cache_lock:
        weather_cache[prediction_type] = {
            "data": prediction_data.copy(),
            "timestamp": datetime.now(),
            "last_update": datetime.now()
        }
        print(f"💾 {prediction_type} 캐시 업데이트 완료: {datetime.now()}")

def generate_prediction_for_cache(prediction_type: str) -> Optional[Dict[Any, Any]]:
    """캐시용 예측 데이터 생성 (백그라운드에서 실행)"""
    try:
        print(f"🔄 백그라운드에서 {prediction_type} 예측 생성 중...")
        
        if model is None or scaler is None:
            print("⚠️ 모델 또는 스케일러가 로드되지 않음")
            return None
        
        # 시간대별 날씨 데이터 생성
        weather_data, target_hour, current_time = get_time_based_weather(prediction_type)
        
        if not weather_data:
            print(f"❌ {prediction_type} 날씨 데이터 생성 실패")
            return None
        
        # WeatherInput 객체 생성
        weather_input = WeatherInput(**weather_data)
        
        # 전처리 및 예측
        processed_data = preprocess_input(weather_input)
        scaled_data = scaler.transform(processed_data)
        prediction_100 = model.predict(scaled_data)[0]
        prediction_10 = convert_score_to_10_scale(prediction_100)
        prediction_10 = np.clip(prediction_10, 0, 10)
        
        # 100점 척도로 변환 (UI 표시용)
        score_100 = convert_score_to_100_scale(prediction_10)
        
        # 등급 결정
        if score_100 >= 80:
            label = "excellent"
        elif score_100 >= 60:
            label = "good"
        elif score_100 >= 50:
            label = "fair"
        else:
            label = "poor"
        
        # 평가 메시지
        evaluation = get_evaluation_message(score_100, prediction_type)
        
        # 시간대별 제목
        titles = {
            "now": "📱 현재 시점 예측",
            "morning": "🌅 출근길 예측 (6-9시)", 
            "evening": "🌆 퇴근길 예측 (18-21시)"
        }
        
        prediction_data = {
            "title": titles[prediction_type],
            "score": round(score_100, 1),
            "score_10": round(prediction_10, 2),
            "label": label,
            "evaluation": evaluation,
            "prediction_time": current_time.strftime("%Y-%m-%d %H:%M"),
            "target_hour": target_hour,
            "weather_data": weather_data,
            "prediction_type": prediction_type,
            "status": "success"
        }
        
        print(f"✅ {prediction_type} 예측 생성 완료: {score_100}/100")
        return prediction_data
        
    except Exception as e:
        print(f"❌ {prediction_type} 예측 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_default_weather_data():
    """API 실패 시 사용할 기본 날씨 데이터"""
    return {
        "timestamp": datetime.now(),
        "temperature": 20.0,
        "humidity": 60.0,
        "pressure": 1013.0,
        "wind_speed": 3.0,
        "wind_direction": 180.0,
        "precipitation": 0.0,
        "visibility": 10000.0,
        "cloud_amount": 5.0,
        "dew_point": 15.0,
        "pm10": 30.0,
        "pm10_grade": "좋음",
        "region": "서울특별시"
    }

def get_time_based_weather(prediction_type):
    """시간대별 날씨 데이터 생성 (실시간 + 단기예보 API 사용 + 폴백 시스템)"""
    kst = pytz.timezone('Asia/Seoul')
    current_time = datetime.now(kst)
    current_hour = current_time.hour
    
    # 시간대별 목표 시간 설정
    if prediction_type == "morning":
        # 출근 시간대 (6-9시) - 내일 오전 7시 기준
        target_date = current_time.date()
        if current_hour >= 10:  # 오전 10시 이후면 내일 출근길 예측
            target_date = target_date + timedelta(days=1)
        target_hour = 7
        
        # 단기예보 데이터 사용
        weather_data = get_forecast_weather_with_pm10(target_date, target_hour)
        
        if not weather_data:
            print("⚠️ 단기예보 실패, 실시간 데이터로 대체")
            weather_data = get_current_weather_real()
            
        if not weather_data:
            print("⚠️ 실시간 데이터도 실패, 기본값 사용")
            weather_data = get_default_weather_data()
        
        weather_data.update({
            "is_morning_rush": 1,
            "is_evening_rush": 0,
            "is_weekend": 1 if target_date.weekday() >= 5 else 0
        })
        
    elif prediction_type == "evening":
        # 퇴근 시간대 (18-21시) - 오늘/내일 저녁 7시 기준
        target_date = current_time.date()
        if current_hour >= 22:  # 오후 10시 이후면 내일 퇴근길 예측
            target_date = target_date + timedelta(days=1)
        target_hour = 19
        
        # 단기예보 데이터 사용
        weather_data = get_forecast_weather_with_pm10(target_date, target_hour)
        
        if not weather_data:
            print("⚠️ 단기예보 실패, 실시간 데이터로 대체")
            weather_data = get_current_weather_real()
            
        if not weather_data:
            print("⚠️ 실시간 데이터도 실패, 기본값 사용")
            weather_data = get_default_weather_data()
        
        weather_data.update({
            "is_morning_rush": 0,
            "is_evening_rush": 1,
            "is_weekend": 1 if target_date.weekday() >= 5 else 0
        })
        
    else:  # now
        # 현재 시점은 실시간 데이터 사용
        weather_data = get_current_weather_real()
        target_hour = current_hour
        
        if not weather_data:
            print("⚠️ 실시간 데이터 실패, 기본값 사용")
            weather_data = get_default_weather_data()
        
        weather_data.update({
            "is_morning_rush": 1 if 6 <= current_hour <= 9 else 0,
            "is_evening_rush": 1 if 18 <= current_hour <= 21 else 0,
            "is_weekend": 1 if current_time.weekday() >= 5 else 0
        })
    
    # 공통 설정
    if weather_data and weather_data.get("temperature") is not None:
        weather_data.update({
            "season": get_current_season(),
            "temp_category": get_temp_category(weather_data["temperature"])
        })
    
    return weather_data, target_hour, current_time

def get_evaluation_message(score, prediction_type):
    """시간대별 맞춤 평가 메시지"""
    if prediction_type == "morning":
        if score >= 80:
            return "완벽한 출근 날씨입니다! 기분 좋은 하루 시작하세요! 🌟"
        elif score >= 60:
            return "쾌적한 출근길이 예상됩니다. 좋은 하루 되세요! 😊"
        elif score >= 50:
            return "출근길이 조금 불편할 수 있어요. 대비하고 나가세요! 😐"
        else:
            return "출근길 날씨가 좋지 않습니다. 각별히 주의하세요! ⚠️"
    elif prediction_type == "evening":
        if score >= 80:
            return "완벽한 퇴근 날씨입니다! 여유롭게 집에 가세요! 🌆"
        elif score >= 60:
            return "쾌적한 퇴근길이 예상됩니다. 좋은 저녁 되세요! 😊"
        elif score >= 50:
            return "퇴근길이 조금 불편할 수 있어요. 안전하게 가세요! 😐"
        else:
            return "퇴근길 날씨가 좋지 않습니다. 각별히 주의하세요! ⚠️"
    else:  # now
        if score >= 80:
            return "지금 날씨가 완벽합니다! 외출하기 좋은 시간이에요! ☀️"
        elif score >= 60:
            return "현재 날씨가 쾌적합니다. 야외활동 추천해요! 😊"
        elif score >= 50:
            return "현재 날씨가 보통입니다. 적당한 외출은 괜찮아요! 😐"
        else:
            return "현재 날씨가 좋지 않습니다. 실내 활동을 권장해요! 🏠"

def convert_score_to_100_scale(score_10):
    """10점 척도를 100점 척도로 변환 (UI 표시용)"""
    return score_10 * 10

# 백그라운드 태스크
def background_cache_updater():
    """백그라운드에서 캐시를 주기적으로 업데이트"""
    global background_task_running
    
    print("🚀 백그라운드 캐시 업데이터 시작")
    background_task_running = True
    
    while background_task_running:
        try:
            print(f"🔄 캐시 업데이트 시작: {datetime.now()}")
            
            # 모든 예측 타입에 대해 캐시 업데이트
            prediction_types = ["now", "morning", "evening"]
            
            # ThreadPoolExecutor로 병렬 처리
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {}
                for pred_type in prediction_types:
                    future = executor.submit(generate_prediction_for_cache, pred_type)
                    futures[pred_type] = future
                
                # 결과 수집 및 캐시 업데이트
                for pred_type, future in futures.items():
                    try:
                        result = future.result(timeout=30)  # 30초 타임아웃으로 단축
                        if result:
                            update_cache(pred_type, result)
                        else:
                            print(f"⚠️ {pred_type} 예측 결과가 None")
                    except Exception as e:
                        print(f"❌ {pred_type} 캐시 업데이트 실패: {e}")
            
            print(f"✅ 캐시 업데이트 완료: {datetime.now()}")
            
            # 다음 업데이트까지 대기
            time.sleep(UPDATE_INTERVAL_MINUTES * 60)
            
        except Exception as e:
            print(f"❌ 백그라운드 캐시 업데이터 오류: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(60)  # 오류 시 1분 후 재시도

def start_background_tasks():
    """백그라운드 태스크 시작 (비블로킹)"""
    global background_task_running
    
    if not background_task_running:
        print("🚀 백그라운드 캐시 시스템 시작")
        
        # 백그라운드 스레드 시작 (초기 캐시 생성도 백그라운드에서)
        cache_thread = threading.Thread(target=background_cache_updater, daemon=True)
        cache_thread.start()
        print("🚀 백그라운드 캐시 업데이터 스레드 시작됨")

def stop_background_tasks():
    """백그라운드 태스크 중지"""
    global background_task_running
    background_task_running = False
    print("🛑 백그라운드 캐시 업데이터 중지됨")

# 앱 시작/종료 시 리소스 관리
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 모델 로드
    load_model_from_s3()
    
    # 백그라운드 캐시 시스템 시작
    start_background_tasks()
    
    yield
    
    # 종료 시 정리 작업
    stop_background_tasks()

app = FastAPI(
    title="Weather Comfort Score API", 
    version="0.1.0",
    description="AI 기반 날씨 쾌적지수 예측 API ",
    lifespan=lifespan
)

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],  # React 개발 서버
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

@app.get("/predict/{prediction_type}")
def predict_by_type(prediction_type: str):
    """시간대별 쾌적지수 예측 (캐시 기반 - 즉시 응답)"""
    if prediction_type not in ["now", "morning", "evening"]:
        raise HTTPException(status_code=400, detail="Invalid prediction type. Use: now, morning, evening")
    
    if model is None or scaler is None:
        raise HTTPException(status_code=503, detail="모델 또는 스케일러가 로드되지 않았습니다")
    
    try:
        # 1순위: 캐시된 데이터 사용 (즉시 응답)
        cached_result = get_cached_prediction(prediction_type)
        if cached_result:
            return cached_result
        
        # 2순위: 캐시가 없거나 만료된 경우 실시간 생성 (폴백)
        print(f"⚠️ {prediction_type} 캐시 없음 - 실시간 생성")
        
        # 시간대별 날씨 데이터 생성
        weather_data, target_hour, current_time = get_time_based_weather(prediction_type)
        
        # WeatherInput 객체 생성
        weather_input = WeatherInput(**weather_data)
        
        # 전처리 및 예측
        processed_data = preprocess_input(weather_input)
        scaled_data = scaler.transform(processed_data)
        prediction_100 = model.predict(scaled_data)[0]
        prediction_10 = convert_score_to_10_scale(prediction_100)
        prediction_10 = np.clip(prediction_10, 0, 10)
        
        # 100점 척도로 변환 (UI 표시용)
        score_100 = convert_score_to_100_scale(prediction_10)
        
        # 등급 결정
        if score_100 >= 80:
            label = "excellent"
        elif score_100 >= 60:
            label = "good"
        elif score_100 >= 50:
            label = "fair"
        else:
            label = "poor"
        
        # 평가 메시지
        evaluation = get_evaluation_message(score_100, prediction_type)
        
        # 시간대별 제목
        titles = {
            "now": "📱 현재 시점 예측",
            "morning": "🌅 출근길 예측 (6-9시)", 
            "evening": "🌆 퇴근길 예측 (18-21시)"
        }
        
        result = {
            "title": titles[prediction_type],
            "score": round(score_100, 1),
            "score_10": round(prediction_10, 2),
            "label": label,
            "evaluation": evaluation,
            "prediction_time": current_time.strftime("%Y-%m-%d %H:%M"),
            "target_hour": target_hour,
            "weather_data": weather_data,
            "prediction_type": prediction_type,
            "status": "success"
        }
        
        # 실시간 생성된 결과를 캐시에 저장
        update_cache(prediction_type, result)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"예측 중 오류 발생: {str(e)}")

@app.get("/weather/current")
def get_current_weather():
    """현재 날씨 정보만 반환 (예측 없이)"""
    try:
        weather_data = get_current_weather_real()
        kst = pytz.timezone('Asia/Seoul')
        current_time = datetime.now(kst)
        
        return {
            "weather": weather_data,
            "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"날씨 정보 조회 실패: {str(e)}")

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

@app.get("/cache/status")
def get_cache_status():
    """캐시 상태 확인"""
    with cache_lock:
        status = {}
        current_time = datetime.now()
        
        for pred_type in ["now", "morning", "evening"]:
            cache_entry = weather_cache.get(pred_type, {})
            last_update = cache_entry.get("last_update")
            
            if last_update:
                elapsed = current_time - last_update
                elapsed_minutes = elapsed.total_seconds() / 60
                is_valid = elapsed_minutes < CACHE_DURATION_MINUTES
            else:
                elapsed_minutes = None
                is_valid = False
            
            status[pred_type] = {
                "has_data": cache_entry.get("data") is not None,
                "last_update": last_update.strftime("%Y-%m-%d %H:%M:%S") if last_update else None,
                "elapsed_minutes": round(elapsed_minutes, 1) if elapsed_minutes else None,
                "is_valid": is_valid,
                "cache_duration_minutes": CACHE_DURATION_MINUTES
            }
        
        return {
            "cache_status": status,
            "background_task_running": background_task_running,
            "update_interval_minutes": UPDATE_INTERVAL_MINUTES,
            "current_time": current_time.strftime("%Y-%m-%d %H:%M:%S")
        }

@app.post("/cache/refresh")
def refresh_cache():
    """캐시 수동 새로고침"""
    try:
        prediction_types = ["now", "morning", "evening"]
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}
            for pred_type in prediction_types:
                future = executor.submit(generate_prediction_for_cache, pred_type)
                futures[pred_type] = future
            
            results = {}
            for pred_type, future in futures.items():
                try:
                    result = future.result(timeout=60)
                    if result:
                        update_cache(pred_type, result)
                        results[pred_type] = "success"
                    else:
                        results[pred_type] = "failed"
                except Exception as e:
                    results[pred_type] = f"error: {str(e)}"
        
        return {
            "message": "캐시 새로고침 완료",
            "results": results,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"캐시 새로고침 실패: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 