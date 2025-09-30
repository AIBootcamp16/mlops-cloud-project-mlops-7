"""Feature builder for weather datasets (ASOS, PM10)."""

from __future__ import annotations

from typing import Dict, Any
import pandas as pd
import numpy as np


def create_ml_dataset(raw_data: Dict[str, Any], include_labels: bool = False) -> pd.DataFrame:
    """
    주어진 원시 기상 데이터를 머신러닝 DataFrame으로 변환합니다.

    Args:
        raw_data: {
            "asos": List[Dict],
            "pm10": List[Dict]
        }
        include_labels: True면 comfort_score(정답) 포함, False면 추론용
    """
    # Convert each raw dataset into DataFrame
    asos_df = pd.DataFrame(raw_data.get("asos", []))
    pm10_df = pd.DataFrame(raw_data.get("pm10", []))

    # observed_at 컬럼을 datetime으로 변환 및 통일
    for df in [asos_df, pm10_df]:
        if not df.empty and "observed_at" in df.columns:
            df["datetime"] = pd.to_datetime(df["observed_at"], utc=True)

    # 각 데이터 타입별로 처리하여 하나의 DataFrame으로 통합
    all_records = []

    # ASOS 데이터 처리
    if not asos_df.empty:
        for _, row in asos_df.iterrows():
            try:
                def safe_float(value):
                    """안전하게 float으로 변환"""
                    if value is None or value == '':
                        return None
                    try:
                        return float(value)
                    except:
                        return None

                record = {
                    "station_id": str(row.get("station_id", "")),
                    "datetime": row.get("datetime"),
                    "temperature": safe_float(row.get("temperature")),
                    "wind_speed": safe_float(row.get("wind_speed")),
                    "humidity": safe_float(row.get("humidity")),
                    "pressure": safe_float(row.get("pressure")),
                    "rainfall": safe_float(row.get("rainfall")),
                    "wind_direction": safe_float(row.get("wind_direction")),
                    "dew_point": safe_float(row.get("dew_point")),
                    "cloud_amount": safe_float(row.get("cloud_amount")),
                    "visibility": safe_float(row.get("visibility")),
                    "sunshine": safe_float(row.get("sunshine")),
                    "pm10": None
                }
                all_records.append(record)
            except:
                continue

    # PM10 데이터 처리
    if not pm10_df.empty:
        for _, row in pm10_df.iterrows():
            try:
                # 기존 레코드에서 같은 station_id와 datetime 찾기
                station_id = str(row.get("station_id", ""))
                datetime_val = row.get("datetime")
                pm10_val = row.get("value")

                # 숫자 검증
                if pm10_val is not None:
                    try:
                        pm10_val = float(pm10_val)
                    except:
                        pm10_val = None

                # 기존 레코드 찾아서 업데이트 또는 새 레코드 생성
                found = False
                for record in all_records:
                    if record["station_id"] == station_id and record["datetime"] == datetime_val:
                        record["pm10"] = pm10_val
                        found = True
                        break

                if not found:
                    record = {
                        "station_id": station_id,
                        "datetime": datetime_val,
                        "temperature": None,
                        "wind_speed": None,
                        "humidity": None,
                        "pressure": None,
                        "rainfall": None,
                        "wind_direction": None,
                        "dew_point": None,
                        "cloud_amount": None,
                        "visibility": None,
                        "sunshine": None,
                        "pm10": pm10_val
                    }
                    all_records.append(record)
            except:
                continue


    # DataFrame 생성
    if all_records:
        merged_df = pd.DataFrame(all_records)

        # 데이터 정리
        merged_df = merged_df.dropna(subset=["datetime"])  # datetime이 없는 행 제거
        merged_df = merged_df.sort_values(["datetime", "station_id"])
        merged_df = merged_df.reset_index(drop=True)

        # 피처 엔지니어링 적용
        merged_df = add_engineered_features(merged_df, include_labels=include_labels)

        return merged_df
    else:
        return pd.DataFrame(columns=[
            "station_id", "datetime", "temperature", "wind_speed", "humidity",
            "pressure", "rainfall", "wind_direction", "dew_point", "cloud_amount",
            "visibility", "sunshine", "pm10"
        ])


def add_engineered_features(df: pd.DataFrame, include_labels: bool = False) -> pd.DataFrame:
    """기본 기상 데이터에 출퇴근 쾌적지수 관련 피처들을 추가합니다."""

    if df.empty:
        return df

    # 복사본 생성
    df = df.copy()

    # 1. 시간 기반 피처들
    df['hour'] = df['datetime'].dt.hour
    df['day_of_week'] = df['datetime'].dt.dayofweek  # 0=월요일, 6=일요일
    df['month'] = df['datetime'].dt.month

    # 출퇴근 시간 여부
    df['is_rush_hour'] = df['hour'].isin([7, 8, 9, 18, 19, 20])
    df['is_morning_rush'] = df['hour'].isin([7, 8, 9])
    df['is_evening_rush'] = df['hour'].isin([18, 19, 20])

    # 평일/주말
    df['is_weekday'] = df['day_of_week'] < 5
    df['is_weekend'] = df['day_of_week'] >= 5

    # 계절 (3,4,5=봄, 6,7,8=여름, 9,10,11=가을, 12,1,2=겨울)
    df['season'] = df['month'].map({
        12: 'winter', 1: 'winter', 2: 'winter',
        3: 'spring', 4: 'spring', 5: 'spring',
        6: 'summer', 7: 'summer', 8: 'summer',
        9: 'autumn', 10: 'autumn', 11: 'autumn'
    })

    # 2. 기온 기반 피처들
    if 'temperature' in df.columns:
        # 온도 구간 (None 값 처리)
        df['temp_category'] = pd.cut(
            df['temperature'].fillna(15),  # None 값을 기본값으로 대체
            bins=[-999, 0, 10, 20, 30, 999],
            labels=['very_cold', 'cold', 'mild', 'warm', 'hot']
        )

        # 쾌적 온도 (20도 기준)
        df['temp_comfort'] = 20 - (df['temperature'] - 20).abs()

        # 극값 여부
        df['temp_extreme'] = (df['temperature'] < 0) | (df['temperature'] > 30)

        # 난방/냉방 필요
        df['heating_needed'] = df['temperature'] < 10
        df['cooling_needed'] = df['temperature'] > 25

    # 3. 지역 기반 피처들 (관측소 코드 기반)
    # 주요 도시 구분 (실제 기상청 관측소 코드 기준)
    metro_stations = ['100', '101', '102', '104', '105', '108', '112', '119', '129', '133']
    coastal_stations = ['102', '104', '115', '130', '131', '152', '156', '159', '168']

    df['is_metro_area'] = df['station_id'].isin(metro_stations)
    df['is_coastal'] = df['station_id'].isin(coastal_stations)

    # 권역 구분 (관측소 번호 기반 간이 구분)
    df['region'] = df['station_id'].astype(str).str[0].map({
        '1': 'central',    # 100번대: 중부권
        '2': 'south',      # 200번대: 남부권
        '3': 'east',       # 300번대: 동부권
        '9': 'west'        # 900번대: 서부권
    }).fillna('other')

    # 4. 대기질 기반 피처들
    if 'pm10' in df.columns:
        # 미세먼지 등급 (환경부 기준, None 값 처리)
        df['pm10_grade'] = pd.cut(
            df['pm10'].fillna(50),  # None 값을 기본값으로 대체
            bins=[0, 30, 80, 150, 999],
            labels=['good', 'moderate', 'unhealthy', 'very_unhealthy']
        )

        # 마스크 필요 여부
        df['mask_needed'] = df['pm10'] > 50

        # 야외활동 적합도
        df['outdoor_activity_ok'] = df['pm10'] <= 80

    # 5. 종합 쾌적지수 계산 (학습용만)
    if include_labels:
        df['comfort_score'] = calculate_comfort_score(df)

    return df


def calculate_comfort_score(df: pd.DataFrame) -> pd.Series:
    """기상 조건을 종합하여 출퇴근 쾌적지수를 계산합니다 (0-100점)."""

    scores = pd.Series(50.0, index=df.index)  # 기본 점수 50점

    # 기온 점수 (가장 중요한 요소, 50% 비중)
    if 'temperature' in df.columns:
        temp_score = df['temperature'].map(lambda x:
            100 if pd.isna(x) else
            90 if 15 <= x <= 22 else  # 최적 온도
            70 if 10 <= x <= 25 else  # 적당한 온도
            50 if 5 <= x <= 30 else   # 견딜만한 온도
            20 if 0 <= x <= 35 else   # 불쾌한 온도
            10  # 극한 온도
        )
        scores = scores * 0.5 + temp_score * 0.5

    # 미세먼지 점수 (30% 비중)
    if 'pm10' in df.columns:
        pm10_score = df['pm10'].map(lambda x:
            50 if pd.isna(x) else  # 데이터 없음은 중립
            90 if x <= 15 else     # 매우 좋음
            70 if x <= 35 else     # 좋음
            50 if x <= 75 else     # 보통
            30 if x <= 150 else    # 나쁨
            10  # 매우 나쁨
        )
        scores = scores * 0.7 + pm10_score * 0.3

    # 출퇴근 시간 보정 (-10점, 혼잡도 반영)
    if 'is_rush_hour' in df.columns:
        scores = scores - (df['is_rush_hour'] * 10)

    # 주말 보정 (+5점, 여유로움)
    if 'is_weekend' in df.columns:
        scores = scores + (df['is_weekend'] * 5)

    # 극한 날씨 보정 (-20점)
    if 'temp_extreme' in df.columns:
        scores = scores - (df['temp_extreme'] * 20)

    # 점수 범위 조정 (0-100)
    scores = np.clip(scores, 0, 100)

    return scores


__all__ = ["create_ml_dataset", "add_engineered_features", "calculate_comfort_score"]
