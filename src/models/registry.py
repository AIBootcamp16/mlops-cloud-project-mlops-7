from __future__ import annotations
from typing import Dict, Any, Union
import logging
from sklearn.base import BaseEstimator
from sklearn.linear_model import LinearRegression, Ridge, Lasso, LogisticRegression, RidgeClassifier
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier

# 외부 라이브러리 import-guard
try:
    from lightgbm import LGBMRegressor, LGBMClassifier
except ImportError:
    LGBMRegressor = LGBMClassifier = None

try:
    from xgboost import XGBRegressor, XGBClassifier
except ImportError:
    XGBRegressor = XGBClassifier = None

try:
    from catboost import CatBoostRegressor, CatBoostClassifier
except ImportError:
    CatBoostRegressor = CatBoostClassifier = None

# 모델 별칭 매핑
MODEL_ALIASES = {
    'randomforest': 'rf',
    'random_forest': 'rf',
    'lightgbm': 'lgbm',
    'xgboost': 'xgb',
    'catboost': 'cat',
    'logistic': 'logistic_regression'
}

def get_model(task: str, name: str, params: Dict[str, Any]) -> BaseEstimator:
    """
    모델 팩토리 함수
    
    Args:
        task: 'regression' 또는 'classification'
        name: 모델 이름
        params: 모델 하이퍼파라미터
    
    Returns:
        sklearn 호환 모델 객체
    
    Raises:
        ValueError: 지원하지 않는 task 또는 model name
        AssertionError: 필수 라이브러리 미설치
    """
    task = task.lower()
    name = name.lower()
    
    # 별칭 처리
    name = MODEL_ALIASES.get(name, name)
    
    logging.info(f"Creating {name} model for {task} task with params: {params}")
    
    if task == "regression":
        return _create_regressor(name, params)
    elif task == "classification":
        return _create_classifier(name, params)
    else:
        raise ValueError(f"Unsupported task: {task}. Use 'regression' or 'classification'")

def _create_regressor(name: str, params: Dict[str, Any]) -> BaseEstimator:
    """회귀 모델 생성"""
    if name == "linear":
        return LinearRegression(**params)
    elif name == "ridge":
        return Ridge(**params)
    elif name == "lasso":
        return Lasso(**params)
    elif name == "rf":
        return RandomForestRegressor(**params)
    elif name == "lgbm":
        assert LGBMRegressor is not None, "lightgbm이 설치되지 않았습니다: pip install lightgbm"
        return LGBMRegressor(**params)
    elif name == "xgb":
        assert XGBRegressor is not None, "xgboost가 설치되지 않았습니다: pip install xgboost"
        return XGBRegressor(**params)
    elif name == "cat":
        assert CatBoostRegressor is not None, "catboost가 설치되지 않았습니다: pip install catboost"
        return CatBoostRegressor(**params)
    else:
        available = ["linear", "ridge", "lasso", "rf", "lgbm", "xgb", "cat"]
        raise ValueError(f"Unknown regressor: {name}. Available: {available}")

def _create_classifier(name: str, params: Dict[str, Any]) -> BaseEstimator:
    """분류 모델 생성"""
    if name == "logistic_regression":
        return LogisticRegression(**params)
    elif name == "ridge_classifier":
        return RidgeClassifier(**params)
    elif name == "rf":
        return RandomForestClassifier(**params)
    elif name == "lgbm":
        assert LGBMClassifier is not None, "lightgbm이 설치되지 않았습니다: pip install lightgbm"
        return LGBMClassifier(**params)
    elif name == "xgb":
        assert XGBClassifier is not None, "xgboost가 설치되지 않았습니다: pip install xgboost"
        return XGBClassifier(**params)
    elif name == "cat":
        assert CatBoostClassifier is not None, "catboost가 설치되지 않았습니다: pip install catboost"
        return CatBoostClassifier(**params)
    else:
        available = ["logistic_regression", "ridge_classifier", "rf", "lgbm", "xgb", "cat"]
        raise ValueError(f"Unknown classifier: {name}. Available: {available}")

def get_available_models(task: str) -> list[str]:
    """사용 가능한 모델 목록 반환"""
    if task.lower() == "regression":
        models = ["linear", "ridge", "lasso", "rf"]
        if LGBMRegressor is not None:
            models.append("lgbm")
        if XGBRegressor is not None:
            models.append("xgb")
        if CatBoostRegressor is not None:
            models.append("cat")
        return models
    
    elif task.lower() == "classification":
        models = ["logistic_regression", "ridge_classifier", "rf"]
        if LGBMClassifier is not None:
            models.append("lgbm")
        if XGBClassifier is not None:
            models.append("xgb")
        if CatBoostClassifier is not None:
            models.append("cat")
        return models
    
    else:
        raise ValueError(f"Unknown task: {task}")

# 사용 예시
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # 회귀 모델 생성
    model = get_model("regression", "lgbm", {"n_estimators": 100})
    print(f"Created model: {type(model).__name__}")
    
    # 사용 가능한 모델 확인
    print("Available regression models:", get_available_models("regression"))
    print("Available classification models:", get_available_models("classification"))