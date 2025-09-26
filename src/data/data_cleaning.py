import os
import sys
sys.path.append('/app')

import boto3
import numpy as np
import pandas as pd
from io import StringIO

from src.data.s3_pull import get_s3_data

def clean_weather_data(df: pd.DataFrame) -> pd.DataFrame:
    """날씨/미세먼지 데이터 컬럼명 변경, 타입 변환, 불필요 컬럼 제거"""

    # 1️⃣ 컬럼명 매핑
    rename_map = {
        "STN": "station_id",
        "datetime": "datetime",
        "TA": "temperature",
        "PM10": "pm10",
        "WS": "wind_speed",
        "HM": "humidity",
        "PS": "pressure",
        "RN": "rainfall",
        "WD": "wind_direction",
        "TD": "dew_point",
        "CA": "cloud_amount",
        "VS": "visibility",
        "SS": "sunshine",
    }
    df = df.rename(columns=rename_map)

    # 2️⃣ 필요한 컬럼만 남기기
    keep_cols = list(rename_map.values())
    df = df[keep_cols]

    # 3️⃣ 타입 변환
    # 관측소 ID → 문자열
    if "station_id" in df.columns:
        df["station_id"] = df["station_id"].astype(str)

    # datetime → pandas datetime
    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")

    # 숫자 변환할 컬럼들
    numeric_cols = [
        "temperature", "pm10", "wind_speed", "humidity",
        "pressure", "rainfall", "wind_direction", "dew_point",
        "cloud_amount", "visibility", "sunshine"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df

def add_time_features(df: pd.DataFrame, dt_col: str = "datetime") -> pd.DataFrame:
    s = pd.to_datetime(df[dt_col], errors="coerce")

    df["hour"] = s.dt.hour.astype("Int64")
    df["day_of_week"] = s.dt.dayofweek.astype("Int64")
    df["month"] = s.dt.month.astype("Int64")

    morning_set = {7, 8, 9}
    evening_set = {18, 19, 20}
    rush_set = morning_set | evening_set

    df["is_morning_rush"] = s.dt.hour.isin(morning_set).astype(int)
    df["is_evening_rush"] = s.dt.hour.isin(evening_set).astype(int)
    df["is_rush_hour"] = s.dt.hour.isin(rush_set).astype(int)

    df["is_weekday"] = (s.dt.dayofweek < 5).astype(int)
    df["is_weekend"] = (s.dt.dayofweek >= 5).astype(int)

    season_map = {
        12: "winter", 1: "winter", 2: "winter",
        3: "spring", 4: "spring", 5: "spring",
        6: "summer", 7: "summer", 8: "summer",
        9: "autumn", 10: "autumn", 11: "autumn",
    }
    df["season"] = s.dt.month.map(season_map)

    return df

def add_temp_features(df: pd.DataFrame, temp_col: str = "temperature") -> pd.DataFrame:
    if temp_col not in df.columns:
        raise KeyError(f"'{temp_col}' 컬럼이 없습니다.")

    temp = pd.to_numeric(df[temp_col], errors="coerce")

    # 1️⃣ 온도 구간 분류
    def categorize_temp(t):
        if pd.isna(t):
            return np.nan
        if t < 0:
            return "very_cold"
        elif t < 10:
            return "cold"
        elif t < 20:
            return "mild"
        elif t < 30:
            return "warm"
        else:
            return "hot"

    df["temp_category"] = temp.apply(categorize_temp)

    # 2️⃣ 쾌적도 점수 (20℃에 가까울수록 높음)
    df["temp_comfort"] = 20 - (temp - 20).abs()

    # 3️⃣ 극한 여부 (<0 or >30) → int
    df["temp_extreme"] = ((temp < 0) | (temp > 30)).astype(int)

    # 4️⃣ 난방 필요 (<10) → int
    df["heating_needed"] = (temp < 10).astype(int)

    # 5️⃣ 냉방 필요 (>25) → int
    df["cooling_needed"] = (temp > 25).astype(int)

    return df

import pandas as pd

def add_region_features(df: pd.DataFrame, station_col: str = "station_id") -> pd.DataFrame:
    """
    지역 기반 파생 피처 생성
    - is_metro_area: 주요 도시 여부 (0/1)
    - is_coastal: 연안 지역 여부 (0/1)
    - region: 관측소 번호 첫 자리 기준 권역 분류
    """

    if station_col not in df.columns:
        raise KeyError(f"'{station_col}' 컬럼이 없습니다.")

    # 문자열화 (숫자로 들어오는 경우 대비)
    stations = df[station_col].astype(str)

    # 1️⃣ 주요 도시 리스트 (예시: 서울, 부산, 대구, 인천, 광주, 대전, 울산 등)
    metro_list = {"108", "159", "143", "112", "156", "133", "152"}  # 예시 ID, 실제는 맞게 채워야 함
    df["is_metro_area"] = stations.isin(metro_list).astype(int)

    # 2️⃣ 연안 지역 리스트 (예시: 속초, 강릉, 포항, 여수, 목포, 제주 등)
    coastal_list = {"90", "100", "136", "168", "184"}  # 예시 ID, 실제는 맞게 채워야 함
    df["is_coastal"] = stations.isin(coastal_list).astype(int)

    # 3️⃣ 관측소 번호 첫자리 기준 권역 분류
    def map_region(stn: str) -> str:
        if not stn or not stn[0].isdigit():
            return "unknown"
        first_digit = stn[0]
        if first_digit in {"1"}:  # 예: 수도권/중부
            return "central"
        elif first_digit in {"2"}:  # 예: 남부
            return "southern"
        elif first_digit in {"3"}:  # 예: 동해안/강원
            return "eastern"
        elif first_digit in {"4"}:  # 예: 서해안/호남
            return "western"
        else:
            return "unknown"

    df["region"] = stations.apply(map_region)

    return df

import pandas as pd

def add_air_quality_features(df: pd.DataFrame, pm10_col: str = "pm10") -> pd.DataFrame:
    if pm10_col not in df.columns:
        raise KeyError(f"'{pm10_col}' 컬럼이 없습니다.")

    pm10 = pd.to_numeric(df[pm10_col], errors="coerce")

    # 1️⃣ 환경부 미세먼지 등급 (µg/m³ 기준)
    def grade_pm10(value):
        if pd.isna(value):
            return "unknown"
        if value <= 30:
            return "good"         # 좋음
        elif value <= 80:
            return "moderate"     # 보통
        elif value <= 150:
            return "bad"          # 나쁨
        else:
            return "very_bad"     # 매우 나쁨

    df["pm10_grade"] = pm10.apply(grade_pm10)

    # 2️⃣ 마스크 필요 여부 (pm10 > 50) → int
    df["mask_needed"] = (pm10 > 50).astype(int)

    # 3️⃣ 야외활동 가능 여부 (pm10 <= 80) → int
    df["outdoor_activity_ok"] = (pm10 <= 80).astype(int)

    return df

import pandas as pd
import numpy as np

def add_comfort_score(df: pd.DataFrame,
                      temp_col: str = "temperature",
                      pm10_col: str = "pm10",
                      rush_col: str = "is_rush_hour",
                      weekend_col: str = "is_weekend",
                      extreme_col: str = "temp_extreme") -> pd.DataFrame:
    """
    종합 쾌적지수 (comfort_score) 생성
    - 기온 50%
    - 미세먼지 30%
    - 보정점수 (출퇴근/주말/극한기온)
    """

    # NaN 방지를 위해 숫자 변환
    temp = pd.to_numeric(df[temp_col], errors="coerce")
    pm10 = pd.to_numeric(df[pm10_col], errors="coerce")

    # 1️⃣ 기온 점수
    def temp_score_fn(t):
        if pd.isna(t):
            return 50
        if 15 <= t <= 22: return 90   # 최적
        elif 10 <= t <= 25: return 70 # 적당
        elif 5 <= t <= 30: return 50  # 견딜만
        elif 0 <= t <= 35: return 20  # 불쾌
        else: return 10               # 극한

    temp_score = temp.apply(temp_score_fn)

    # 2️⃣ 미세먼지 점수
    def pm10_score_fn(v):
        if pd.isna(v):
            return 50
        if v <= 15: return 90       # 매우 좋음
        elif v <= 35: return 70     # 좋음
        elif v <= 75: return 50     # 보통
        elif v <= 150: return 30    # 나쁨
        else: return 10             # 매우 나쁨

    pm10_score = pm10.apply(pm10_score_fn)

    # 3️⃣ 기본 점수
    base_score = 80.0
    comfort = base_score * 0.5 + temp_score * 0.5
    comfort = comfort * 0.7 + pm10_score * 0.3

    # 4️⃣ 보정값
    rush = df[rush_col].astype(int) if rush_col in df.columns else 0
    weekend = df[weekend_col].astype(int) if weekend_col in df.columns else 0
    extreme = df[extreme_col].astype(int) if extreme_col in df.columns else 0

    comfort = comfort - rush * 10
    comfort = comfort + weekend * 5
    comfort = comfort - extreme * 20

    # 5️⃣ 0~100 범위로 제한
    df["comfort_score"] = comfort.clip(lower=0, upper=100)

    return df


def save_to_s3(df, bucket, key, sep=","):
    """DataFrame을 CSV로 변환 후 S3에 업로드"""
    # 1️⃣ DataFrame → CSV 문자열 변환
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, sep=sep, encoding="utf-8")

    # 2️⃣ S3 클라이언트 생성
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION")
    )

    # 3️⃣ 업로드 실행
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=csv_buffer.getvalue()
    )
    print(f"✅ S3 업로드 완료: s3://{bucket}/{key}")


if __name__ == "__main__":
    # 데이터 생성 (네가 만든 전처리 함수들 실행)
    weather_df = clean_weather_data(get_s3_data())
    weather_df = add_time_features(weather_df)
    weather_df = add_temp_features(weather_df)
    weather_df = add_air_quality_features(weather_df)
    weather_df = add_region_features(weather_df)
    weather_df = add_comfort_score(weather_df)

    # CSV → S3 저장
    save_to_s3(
        weather_df,
        bucket="weather-mlops-team-data",
        key="ml_dataset/weather_features_full.csv"
    )
