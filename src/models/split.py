import os
import sys
sys.path.append('/app')

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from src.data.s3_pull_processed import get_processed_data
from src.utils.utils import set_seed

def split_and_scale_data(test_size=0.2, val_size=0.2, random_state=42):
    """
    S3에서 데이터 로드 후 train/val/test 분할 및 스케일링
    
    Args:
        test_size: 테스트 데이터 비율
        val_size: 검증 데이터 비율 
        random_state: 랜덤 시드
        
    Returns:
        tuple: (X_train, X_val, X_test, y_train, y_val, y_test, scaler)
    """
    print("🔄 S3에서 데이터 로드 중...")
    
    # 시드 고정
    set_seed(random_state)
    
    # S3에서 피처 엔지니어링된 데이터 로드
    df = get_processed_data()
    print(f"데이터 로드 완료: {df.shape}")
    
    # 타겟 변수 설정 (쾌적지수 예측)
    target_col = "comfort_score"
    exclude_cols = [target_col, "pm10", "datetime", "station_id"]  # pm10도 제외
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    # 결측치 처리 (-99, -9를 NaN으로 변환)
    X = df[feature_cols].copy()
    X = X.replace([-99, -9], np.nan)
    
    # 결측치 비율이 높은 컬럼 제거 (50% 이상)
    high_missing_cols = []
    for col in X.columns:
        missing_ratio = X[col].isnull().sum() / len(X)
        if missing_ratio > 0.5:  # 50% 이상 결측치면 제거
            high_missing_cols.append(col)
    
    if high_missing_cols:
        print(f"결측치 많은 컬럼 제거: {high_missing_cols}")
        X = X.drop(columns=high_missing_cols)
        feature_cols = [col for col in feature_cols if col not in high_missing_cols]
    
    # 나머지 결측치는 평균값으로 대체 (수치형만)
    numeric_cols = X.select_dtypes(include=[np.number]).columns
    X[numeric_cols] = X[numeric_cols].fillna(X[numeric_cols].mean())
    
    # 범주형 변수 원핫인코딩
    categorical_cols = ['season', 'temp_category', 'pm10_grade', 'region']
    categorical_cols = [col for col in categorical_cols if col in X.columns]
    
    if categorical_cols:
        print(f"원핫인코딩 적용: {categorical_cols}")
        X = pd.get_dummies(X, columns=categorical_cols, drop_first=True)
    
    y = df[target_col].fillna(df[target_col].mean())
    
    print(f"피처: {len(feature_cols)}개, 샘플: {len(X)}개")
    
    # Train/Test 분할
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    
    # Train/Val 분할
    val_ratio = val_size / (1 - test_size)
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=val_ratio, random_state=random_state
    )
    
    print(f"Train: {X_train.shape}, Val: {X_val.shape}, Test: {X_test.shape}")
    
    # 스케일링
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    print("✅ 데이터 분할 및 스케일링 완료")
    
    # 원핫인코딩 후 피처 컬럼 목록 저장
    feature_columns = list(X.columns)
    
    return X_train_scaled, X_val_scaled, X_test_scaled, y_train, y_val, y_test, scaler, feature_columns

if __name__ == "__main__":
    split_and_scale_data()




