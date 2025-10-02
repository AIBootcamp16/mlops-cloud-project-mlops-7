import numpy as np
import pandas as pd

def preprocess_for_prediction(df, feature_columns):
    """split.py와 동일한 후처리 로직 + 컬럼 맞추기"""
    print("🔧 전처리 시작")
    
    # 카테고리 이름 통일
    if 'pm10_grade' in df.columns:
        df['pm10_grade'] = df['pm10_grade'].replace({
            'unhealthy': 'bad',
            'very_unhealthy': 'very_bad'
        })

    # 타겟 제외
    target_col = "comfort_score"
    exclude_cols = [target_col, "pm10", "datetime", "station_id"]
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    X = df[feature_cols].copy()
    X = X.replace([-99, -9], np.nan)
    
    # 고결측 컬럼 제거 (50% 이상)
    high_missing_cols = [col for col in X.columns if X[col].isnull().sum() / len(X) > 0.5]
    if high_missing_cols:
        print(f"고결측 컬럼 제거: {high_missing_cols}")
        X = X.drop(columns=high_missing_cols)
    
    # 결측치 평균 대체
    numeric_cols = X.select_dtypes(include=[np.number]).columns
    X[numeric_cols] = X[numeric_cols].fillna(X[numeric_cols].mean())
    
    # 원핫인코딩
    categorical_cols = ['season', 'temp_category', 'pm10_grade', 'region']
    categorical_cols = [col for col in categorical_cols if col in X.columns]
    
    if categorical_cols:
        print(f"원핫인코딩: {categorical_cols}")
        X = pd.get_dummies(X, columns=categorical_cols, drop_first=True)
    
    # 학습 시 컬럼에 맞춰 보정
    for col in feature_columns:
        if col not in X.columns:
            X[col] = 0
    X = X[feature_columns]  # 순서까지 동일하게
    
    print(f"✅ 전처리 완료: {X.shape}")
    return X