from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor
from lightgbm import LGBMRegressor
from xgboost import XGBRegressor
from catboost import CatBoostRegressor

def get_model(name, params=None, random_state=42):
    """모델 팩토리 함수"""
    if params is None:
        params = {}
    
    if name == 'linear':
        return LinearRegression(**params)
    elif name == 'ridge':
        return Ridge(random_state=random_state, **params)
    elif name == 'lasso':
        return Lasso(random_state=random_state, **params)
    elif name == 'rf':
        return RandomForestRegressor(random_state=random_state, **params)
    elif name == 'lgbm':
        return LGBMRegressor(random_state=random_state, verbose=-1, **params)
    elif name == 'xgb':
        return XGBRegressor(random_state=random_state, **params)
    elif name == 'cat':
        return CatBoostRegressor(random_state=random_state, verbose=False,train_dir=None, **params)
    else:
        raise ValueError(f"Unknown model: {name}")