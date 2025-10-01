"""
전체 파이프라인 (Raw → Feature Engineering → Preprocessing → Model)
완전 자동화: 모든 로직을 sklearn transformer로 변환하여 pkl 저장 가능
"""
import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline


class RawDataCleaner(BaseEstimator, TransformerMixin):
    """
    data_cleaning.py의 clean_weather_data() 로직
    Raw 데이터 → 정제된 데이터
    """
    
    def __init__(self):
        self.rename_map = {
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
        
    def fit(self, X, y=None):
        return self
        
    def transform(self, X):
        df = X.copy() if isinstance(X, pd.DataFrame) else pd.DataFrame(X)
        
        # 컬럼명 변경
        df = df.rename(columns=self.rename_map)
        
        # 필요한 컬럼만 남기기
        keep_cols = list(self.rename_map.values())
        df = df[[col for col in keep_cols if col in df.columns]]
        
        # 타입 변환
        if "station_id" in df.columns:
            df["station_id"] = df["station_id"].astype(str)
            
        if "datetime" in df.columns:
            df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
            
        numeric_cols = [
            "temperature", "pm10", "wind_speed", "humidity",
            "pressure", "rainfall", "wind_direction", "dew_point",
            "cloud_amount", "visibility", "sunshine"
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
                
        return df


class TimeFeatureEngineer(BaseEstimator, TransformerMixin):
    """
    data_cleaning.py의 add_time_features() 로직
    """
    
    def __init__(self, dt_col="datetime"):
        self.dt_col = dt_col
        
    def fit(self, X, y=None):
        return self
        
    def transform(self, X):
        df = X.copy() if isinstance(X, pd.DataFrame) else pd.DataFrame(X)
        s = pd.to_datetime(df[self.dt_col], errors="coerce")
        
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


class TemperatureFeatureEngineer(BaseEstimator, TransformerMixin):
    """
    data_cleaning.py의 add_temp_features() 로직
    """
    
    def __init__(self, temp_col="temperature"):
        self.temp_col = temp_col
        
    def fit(self, X, y=None):
        return self
        
    def transform(self, X):
        df = X.copy() if isinstance(X, pd.DataFrame) else pd.DataFrame(X)
        temp = pd.to_numeric(df[self.temp_col], errors="coerce")
        
        # 온도 구간 분류
        def categorize_temp(t):
            if pd.isna(t):
                return np.nan
            if t < 0: return "very_cold"
            elif t < 10: return "cold"
            elif t < 20: return "mild"
            elif t < 30: return "warm"
            else: return "hot"
            
        df["temp_category"] = temp.apply(categorize_temp)
        df["temp_comfort"] = 20 - (temp - 20).abs()
        df["temp_extreme"] = ((temp < 0) | (temp > 30)).astype(int)
        df["heating_needed"] = (temp < 10).astype(int)
        df["cooling_needed"] = (temp > 25).astype(int)
        
        return df


class AirQualityFeatureEngineer(BaseEstimator, TransformerMixin):
    """
    data_cleaning.py의 add_air_quality_features() 로직
    """
    
    def __init__(self, pm10_col="pm10"):
        self.pm10_col = pm10_col
        
    def fit(self, X, y=None):
        return self
        
    def transform(self, X):
        df = X.copy() if isinstance(X, pd.DataFrame) else pd.DataFrame(X)
        pm10 = pd.to_numeric(df[self.pm10_col], errors="coerce")
        
        def grade_pm10(value):
            if pd.isna(value): return "unknown"
            if value <= 30: return "good"
            elif value <= 80: return "moderate"
            elif value <= 150: return "bad"
            else: return "very_bad"
            
        df["pm10_grade"] = pm10.apply(grade_pm10)
        df["mask_needed"] = (pm10 > 50).astype(int)
        df["outdoor_activity_ok"] = (pm10 <= 80).astype(int)
        
        return df


class RegionFeatureEngineer(BaseEstimator, TransformerMixin):
    """
    data_cleaning.py의 add_region_features() 로직
    """
    
    def __init__(self, station_col="station_id"):
        self.station_col = station_col
        
    def fit(self, X, y=None):
        return self
        
    def transform(self, X):
        df = X.copy() if isinstance(X, pd.DataFrame) else pd.DataFrame(X)
        stations = df[self.station_col].astype(str)
        
        metro_list = {"108", "159", "143", "112", "156", "133", "152"}
        df["is_metro_area"] = stations.isin(metro_list).astype(int)
        
        coastal_list = {"90", "100", "136", "168", "184"}
        df["is_coastal"] = stations.isin(coastal_list).astype(int)
        
        def map_region(stn: str) -> str:
            if not stn or not stn[0].isdigit():
                return "unknown"
            first_digit = stn[0]
            if first_digit in {"1"}: return "central"
            elif first_digit in {"2"}: return "southern"
            elif first_digit in {"3"}: return "eastern"
            elif first_digit in {"4"}: return "western"
            else: return "unknown"
            
        df["region"] = stations.apply(map_region)
        
        return df


class ComfortScoreCalculator(BaseEstimator, TransformerMixin):
    """
    data_cleaning.py의 add_comfort_score() 로직
    타겟 변수 생성
    """
    
    def __init__(self, 
                 temp_col="temperature",
                 pm10_col="pm10",
                 rush_col="is_rush_hour",
                 weekend_col="is_weekend",
                 extreme_col="temp_extreme"):
        self.temp_col = temp_col
        self.pm10_col = pm10_col
        self.rush_col = rush_col
        self.weekend_col = weekend_col
        self.extreme_col = extreme_col
        
    def fit(self, X, y=None):
        return self
        
    def transform(self, X):
        df = X.copy() if isinstance(X, pd.DataFrame) else pd.DataFrame(X)
        
        temp = pd.to_numeric(df[self.temp_col], errors="coerce")
        pm10 = pd.to_numeric(df[self.pm10_col], errors="coerce")
        
        # 기온 점수
        def temp_score_fn(t):
            if pd.isna(t): return 50
            if 15 <= t <= 22: return 90
            elif 10 <= t <= 25: return 70
            elif 5 <= t <= 30: return 50
            elif 0 <= t <= 35: return 20
            else: return 10
            
        temp_score = temp.apply(temp_score_fn)
        
        # 미세먼지 점수
        def pm10_score_fn(v):
            if pd.isna(v): return 50
            if v <= 15: return 90
            elif v <= 35: return 70
            elif v <= 75: return 50
            elif v <= 150: return 30
            else: return 10
            
        pm10_score = pm10.apply(pm10_score_fn)
        
        # 기본 점수
        base_score = 80.0
        comfort = base_score * 0.5 + temp_score * 0.5
        comfort = comfort * 0.7 + pm10_score * 0.3
        
        # 보정값
        rush = df[self.rush_col].astype(int) if self.rush_col in df.columns else 0
        weekend = df[self.weekend_col].astype(int) if self.weekend_col in df.columns else 0
        extreme = df[self.extreme_col].astype(int) if self.extreme_col in df.columns else 0
        
        comfort = comfort - rush * 10
        comfort = comfort + weekend * 5
        comfort = comfort - extreme * 20
        
        df["comfort_score"] = comfort.clip(lower=0, upper=100)
        
        return df


def create_full_feature_engineering_pipeline():
    """
    Raw 데이터 → Feature Engineered 데이터
    전체 피처 엔지니어링 파이프라인 생성
    
    이 파이프라인을 pkl로 저장하면 완전 자동화!
    """
    pipeline = Pipeline([
        ('clean', RawDataCleaner()),
        ('time_features', TimeFeatureEngineer()),
        ('temp_features', TemperatureFeatureEngineer()),
        ('air_quality', AirQualityFeatureEngineer()),
        ('region', RegionFeatureEngineer()),
        ('comfort_score', ComfortScoreCalculator()),
    ])
    
    return pipeline


if __name__ == "__main__":
    print("✅ Full Feature Engineering Pipeline 모듈 로드 성공")
    print("사용법: create_full_feature_engineering_pipeline()") 