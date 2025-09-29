import os
import sys
sys.path.append('/app')

import pandas as pd
import numpy as np
import pickle
import datetime
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error
import fire
import wandb

from src.models.split import split_and_scale_data
from src.utils.utils import set_seed, save_model_to_s3
from src.utils.model_utils import get_model
from src.utils.wandb_utils import get_latest_run_name, get_requirements



def tune_rf_hyperparameters(
    search_type="grid",  # "grid" or "random"
    cv_folds=3,
    n_iter=20,  # RandomizedSearchCV용
    test_size=0.2,
    val_size=0.2,
    random_state=42,
    wandb_project=None
):
    """
    Random Forest 하이퍼파라미터 튜닝
    
    Args:
        search_type: "grid" 또는 "random"
        cv_folds: Cross-validation folds 수
        n_iter: RandomizedSearchCV 반복 횟수
        test_size: 테스트 데이터 비율
        val_size: 검증 데이터 비율  
        random_state: 랜덤 시드
        wandb_project: wandb 프로젝트명
    """
    # 시드 고정
    set_seed(random_state)
    
    # wandb 초기화
    entity = os.getenv('WANDB_ENTITY') or 'realtheai-insight-'
    wandb_project = wandb_project or os.getenv('WANDB_PROJECT') or 'weather-predictor'
    
    # 실험명 생성 (tune 접두사 사용)
    latest_run_name = get_latest_run_name(entity, wandb_project, prefix="rf-tune")
    if latest_run_name == "rf-tune-000":
        experiment_name = "rf-tune-001"
    else:
        num = int(latest_run_name.split("-")[-1]) + 1
        experiment_name = f"rf-tune-{str(num).zfill(3)}"
    
    wandb.init(entity=entity, project=wandb_project, name=experiment_name)
    
    print(f"🚀 RF 하이퍼파라미터 튜닝 시작... ({search_type.upper()})")
    
    # 1. 데이터 로드
    X_train, X_val, X_test, y_train, y_val, y_test, scaler = split_and_scale_data(
        test_size=test_size, val_size=val_size, random_state=random_state
    )
    
    # 학습용 데이터 결합 (train + val)
    X_train_full = np.vstack([X_train, X_val])
    y_train_full = np.hstack([y_train, y_val])
    
    print(f"튜닝용 데이터: {X_train_full.shape}, 테스트: {X_test.shape}")
    
    # 2. 하이퍼파라미터 그리드 정의
    param_grid = {
        'n_estimators': [100, 200, 300],
        'max_depth': [10, 15, 20, None],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4],
        'max_features': ['sqrt', 'log2', None]
    }
    
    # RandomizedSearch용 더 넓은 범위
    param_random = {
        'n_estimators': [50, 100, 150, 200, 300, 400],
        'max_depth': [5, 10, 15, 20, 25, None],
        'min_samples_split': [2, 5, 10, 15, 20],
        'min_samples_leaf': [1, 2, 4, 6, 8],
        'max_features': ['sqrt', 'log2', None, 0.3, 0.5, 0.7]
    }
    
    # 3. 모델 및 서치 객체 생성
    rf = RandomForestRegressor(random_state=random_state, n_jobs=-1)
    
    if search_type == "grid":
        search = GridSearchCV(
            rf, param_grid, 
            cv=cv_folds, 
            scoring='neg_mean_squared_error',
            n_jobs=-1, 
            verbose=1
        )
        params_used = param_grid
    else:  # random
        search = RandomizedSearchCV(
            rf, param_random,
            n_iter=n_iter,
            cv=cv_folds,
            scoring='neg_mean_squared_error',
            n_jobs=-1,
            verbose=1,
            random_state=random_state
        )
        params_used = param_random
    
    # 4. 하이퍼파라미터 서치 실행
    print(f"📊 {search_type.upper()} 서치 실행 중...")
    search.fit(X_train_full, y_train_full)
    
    # 5. 최적 모델로 테스트 평가
    best_model = search.best_estimator_
    
    # 예측
    train_pred = best_model.predict(X_train_full)
    test_pred = best_model.predict(X_test)
    
    # 평가 지표 계산
    train_rmse = np.sqrt(mean_squared_error(y_train_full, train_pred))
    test_rmse = np.sqrt(mean_squared_error(y_test, test_pred))
    train_mae = mean_absolute_error(y_train_full, train_pred)
    test_mae = mean_absolute_error(y_test, test_pred)
    
    # CV 점수
    cv_rmse = np.sqrt(-search.best_score_)
    
    print(f"\n🏆 최적 하이퍼파라미터:")
    for param, value in search.best_params_.items():
        print(f"   {param}: {value}")
    
    print(f"\n📊 성능 결과:")
    print(f"   CV RMSE: {cv_rmse:.4f}")
    print(f"   Train RMSE: {train_rmse:.4f}")
    print(f"   Test RMSE: {test_rmse:.4f}")
    
    # 6. WANDB 로깅
    wandb.log({
        "search_type": search_type,
        "cv_folds": cv_folds,
        "cv_rmse": cv_rmse,
        "train_rmse": train_rmse,
        "test_rmse": test_rmse,
        "train_mae": train_mae,
        "test_mae": test_mae,
        **{f"best_{k}": v for k, v in search.best_params_.items()}
    })
    
    # 상위 5개 결과도 로깅
    results_df = pd.DataFrame(search.cv_results_)
    top_5 = results_df.nlargest(5, 'mean_test_score')
    
    for i, (idx, row) in enumerate(top_5.iterrows()):
        wandb.log({f"top_{i+1}_cv_rmse": np.sqrt(-row['mean_test_score'])})
    
    # 7. 최적 모델 S3 저장
    current_time = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
    
    model_data = {
        "model": best_model,
        "scaler": scaler,
        "model_name": "rf_tuned",
        "metrics": {
            "cv_rmse": cv_rmse,
            "train_rmse": train_rmse,
            "test_rmse": test_rmse,
            "train_mae": train_mae,
            "test_mae": test_mae
        },
        "experiment_name": experiment_name,
        "wandb_project": wandb_project,
        "timestamp": current_time,
        "hyperparameters": search.best_params_,
        "tuning_info": {
            "search_type": search_type,
            "cv_folds": cv_folds,
            "param_space": params_used,
            "n_iter": n_iter if search_type == "random" else "all_combinations"
        },
        "data_info": {
            "target": "comfort_score",
            "model_type": "regression_tuned",
            "train_samples": len(y_train_full),
            "test_samples": len(y_test),
            "features": X_train_full.shape[1]
        },
        "requirements": get_requirements()
    }
    
    base_path = f"models/{experiment_name}"
    save_model_to_s3(model_data, os.getenv('S3_BUCKET'), base_path)
    
    wandb.finish()
    print("🎉 하이퍼파라미터 튜닝 완료!")
    
    return best_model, search.best_params_, cv_rmse


if __name__ == "__main__":
    fire.Fire(tune_rf_hyperparameters) 