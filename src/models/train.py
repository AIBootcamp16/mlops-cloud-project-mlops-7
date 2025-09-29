import os
import sys
sys.path.append('/app')

import pandas as pd
import numpy as np
import pickle
import datetime
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor
from lightgbm import LGBMRegressor
from xgboost import XGBRegressor
from catboost import CatBoostRegressor
import fire
import wandb

from src.models.split import split_and_scale_data
from src.utils.utils import set_seed, auto_increment_run_suffix, save_model_to_s3
from src.utils.wandb_utils import get_latest_run_name, get_requirements
from src.utils.model_utils import get_model




def train_models(
    model_names=['linear', 'ridge', 'lasso', 'rf', 'lgbm', 'xgb', 'cat'],
    test_size=0.2,
    val_size=0.2,
    random_state=42,
    wandb_project=None
):
    """
    여러 모델 학습 및 평가 후 베스트 모델 S3 저장
    
    Args:
        model_names: 학습할 모델 리스트
        test_size: 테스트 데이터 비율
        val_size: 검증 데이터 비율
        random_state: 랜덤 시드
        wandb_project: wandb 프로젝트명
    """
    # 시드 고정
    set_seed(random_state)
    
    # wandb 초기화 (최신 실험명 기반)
    entity = os.getenv('WANDB_ENTITY') or 'realtheai-insight-'
    wandb_project = wandb_project or os.getenv('WANDB_PROJECT') or 'weather-predictor'

    # wandb 확인
    if not entity or not wandb_project:
        raise RuntimeError("WANDB_ENTITY / WANDB_PROJECT를 설정하세요.")
    
    prefix = wandb_project
    latest_run_name = get_latest_run_name(entity, wandb_project,prefix=prefix)
    experiment_name = auto_increment_run_suffix(latest_run_name, default_prefix=prefix)
    wandb.init(entity=entity, project=wandb_project, name=experiment_name)
    
    print("🚀 모델 학습 시작...")
    
    # 1. 데이터 로드 (split.py 활용)
    X_train, X_val, X_test, y_train, y_val, y_test, scaler = split_and_scale_data(
        test_size=test_size, val_size=val_size, random_state=random_state
    )
    
    # 2. 모델별 학습 및 평가 (models_plan.md 참조)
    results = {}
    models = {}
    
    for model_name in model_names:
        print(f"\n📊 {model_name.upper()} 모델 학습 중...")
        
        # 모델 생성
        model = get_model(model_name, random_state=random_state)
        
        # 학습
        model.fit(X_train, y_train)
        
        # 예측
        train_pred = model.predict(X_train)
        val_pred = model.predict(X_val)
        test_pred = model.predict(X_test)
        
        # 평가 지표 계산
        train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
        val_rmse = np.sqrt(mean_squared_error(y_val, val_pred))
        test_rmse = np.sqrt(mean_squared_error(y_test, test_pred))
        
        train_mae = mean_absolute_error(y_train, train_pred)
        val_mae = mean_absolute_error(y_val, val_pred)
        test_mae = mean_absolute_error(y_test, test_pred)
        
        # 결과 저장
        result = {
            'train_rmse': train_rmse,
            'val_rmse': val_rmse,
            'test_rmse': test_rmse,
            'train_mae': train_mae,
            'val_mae': val_mae,
            'test_mae': test_mae
        }
        results[model_name] = result
        models[model_name] = model
        
        # wandb 로깅
        wandb.log({
            f"{model_name}_train_rmse": train_rmse,
            f"{model_name}_val_rmse": val_rmse,
            f"{model_name}_test_rmse": test_rmse,
            f"{model_name}_train_mae": train_mae,
            f"{model_name}_val_mae": val_mae,
            f"{model_name}_test_mae": test_mae
        })
        
        print(f"✅ {model_name}: Val RMSE={val_rmse:.4f}, Test RMSE={test_rmse:.4f}")
    
    # 3. 베스트 모델 선택 (Validation RMSE 기준)
    best_model_name = min(results.keys(), key=lambda x: results[x]['val_rmse'])
    best_model = models[best_model_name]
    best_result = results[best_model_name]
    
    print(f"\n🏆 베스트 모델: {best_model_name.upper()}")
    print(f"   Val RMSE: {best_result['val_rmse']:.4f}")
    print(f"   Test RMSE: {best_result['test_rmse']:.4f}")
    
    # wandb에 베스트 모델 로깅
    wandb.log({
        "best_model": best_model_name,
        "best_val_rmse": best_result['val_rmse'],
        "best_test_rmse": best_result['test_rmse']
    })
    
    # 4. 베스트 모델 체계적 구조로 S3 저장
    current_time = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
    
    # 하이퍼파라미터 추출 (모델별로)
    hyperparameters = {}
    if hasattr(best_model, 'get_params'):
        hyperparameters = best_model.get_params()
    
    model_data = {
        "model": best_model,
        "scaler": scaler,
        "model_name": best_model_name,
        "metrics": best_result,
        "experiment_name": experiment_name,
        "wandb_project": wandb_project,
        "timestamp": current_time,
        "hyperparameters": hyperparameters,
        "data_info": {
            "target": "comfort_score",
            "model_type": "regression",
            "train_samples": len(y_train),
            "val_samples": len(y_val),
            "test_samples": len(y_test),
            "features": X_train.shape[1]
        },
        "requirements": get_requirements()
    }
    
    base_path = f"models/{experiment_name}"
    save_model_to_s3(model_data, os.getenv('S3_BUCKET'), base_path)
    
    wandb.finish()
    print("🎉 학습 완료!")
    
    return best_model, best_result

if __name__ == "__main__":
    fire.Fire(train_models)
