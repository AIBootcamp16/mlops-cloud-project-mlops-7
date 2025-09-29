import os
import sys
sys.path.append('/app')

import numpy as np
import yaml
import datetime
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from sklearn.metrics import mean_squared_error, mean_absolute_error
import fire
import wandb

from src.models.split import split_and_scale_data
from src.utils.utils import set_seed, save_model_to_s3, auto_increment_run_suffix
from src.utils.model_utils import get_model
from src.utils.wandb_utils import get_latest_run_name, get_requirements


def tune_hyperparameters(
    model_name="rf",
    search_type="grid",
    cv_folds=3,
    n_iter=20,
    test_size=0.2,
    val_size=0.2,
    random_state=42,
    config_path="/app/src/config/hyperparams.yml"
):
    """
    하이퍼파라미터 튜닝
    
    Example:
        python tune_hyperparameters.py --model_name=rf --search_type=grid
        python tune_hyperparameters.py --model_name=lgbm --search_type=random --n_iter=50
    """
    set_seed(random_state)
    
    # 1. YAML에서 파라미터 로드
    with open(config_path, 'r') as f:
        all_params = yaml.safe_load(f)
    
    param_space = all_params[model_name][search_type]
    
    # 2. WandB 초기화
    entity = os.getenv('WANDB_ENTITY', 'realtheai-insight-')
    project = os.getenv('WANDB_PROJECT', 'weather-predictor')
    
    prefix = f"{model_name}-tune"
    latest = get_latest_run_name(entity, project, prefix=prefix)
    exp_name = auto_increment_run_suffix(latest, default_prefix=prefix)
    
    wandb.init(entity=entity, project=project, name=exp_name)
    print(f"🚀 [{model_name.upper()}] 튜닝 시작: {exp_name} ({search_type})")
    
    # 3. 데이터 로드 및 결합
    X_train, X_val, X_test, y_train, y_val, y_test, scaler = split_and_scale_data(
        test_size=test_size, val_size=val_size, random_state=random_state
    )
    X_train_full = np.vstack([X_train, X_val])
    y_train_full = np.hstack([y_train, y_val])
    
    # 4. 모델 튜닝
    base_model = get_model(model_name, random_state=random_state)
    
    if search_type == "grid":
        search = GridSearchCV(base_model, param_space, cv=cv_folds, 
                            scoring='neg_mean_squared_error', n_jobs=-1, verbose=1)
    else:
        search = RandomizedSearchCV(base_model, param_space, n_iter=n_iter, cv=cv_folds,
                                   scoring='neg_mean_squared_error', n_jobs=-1, 
                                   verbose=1, random_state=random_state)
    
    search.fit(X_train_full, y_train_full)
    best_model = search.best_estimator_
    
    # 🆕 각 하이퍼파라미터 조합의 CV 결과를 WandB에 로깅
    print("\n📊 각 조합의 성능을 WandB에 로깅 중...")
    for i, (params, mean_score, std_score) in enumerate(zip(
        search.cv_results_['params'],
        search.cv_results_['mean_test_score'],
        search.cv_results_['std_test_score']
    )):
        cv_rmse_iter = np.sqrt(-mean_score)  # negative MSE를 RMSE로 변환
        cv_std_iter = np.sqrt(std_score)
        
        log_dict = {
            "iteration": i,
            "cv_rmse": cv_rmse_iter,
            "cv_std": cv_std_iter,
        }
        
        # 각 파라미터를 개별적으로 로깅
        for param_name, param_value in params.items():
            log_dict[f"param_{param_name}"] = param_value
        
        wandb.log(log_dict)
    
    print(f"✅ {len(search.cv_results_['params'])}개 조합 로깅 완료!")
    
    # 5. 평가
    train_pred = best_model.predict(X_train_full)
    test_pred = best_model.predict(X_test)
    
    cv_rmse = np.sqrt(-search.best_score_)
    train_rmse = np.sqrt(mean_squared_error(y_train_full, train_pred))
    test_rmse = np.sqrt(mean_squared_error(y_test, test_pred))
    train_mae = mean_absolute_error(y_train_full, train_pred)
    test_mae = mean_absolute_error(y_test, test_pred)
    
    # 6. 결과 출력
    print(f"\n🏆 최적 파라미터: {search.best_params_}")
    print(f"📊 CV RMSE: {cv_rmse:.4f} | Test RMSE: {test_rmse:.4f}")
    
    # 7. 최종 결과 로깅 (Summary로 기록)
    wandb.run.summary.update({
        "best_cv_rmse": cv_rmse,
        "best_train_rmse": train_rmse,
        "best_test_rmse": test_rmse,
        "best_train_mae": train_mae,
        "best_test_mae": test_mae,
        **{f"best_{k}": v for k, v in search.best_params_.items()}
    })
    
    # 8. S3 저장
    model_data = {
        "model": best_model,
        "scaler": scaler,
        "model_name": f"{model_name}_tuned",
        "metrics": {
            "cv_rmse": cv_rmse,
            "train_rmse": train_rmse,
            "test_rmse": test_rmse,
            "train_mae": train_mae,
            "test_mae": test_mae,
        },
        "experiment_name": exp_name,
        "wandb_project": project,
        "timestamp": datetime.datetime.now().strftime("%y%m%d_%H%M%S"),
        "hyperparameters": search.best_params_,
        "tuning_info": {
            "search_type": search_type,
            "cv_folds": cv_folds,
            "param_space": param_space,
            "n_iter": search.n_iter if search_type == "random" else "all_combinations",
        },
        "data_info": {
            "target": "comfort_score",
            "model_type": "regression_tuned",
            "train_samples": len(y_train_full),
            "test_samples": len(y_test),
            "features": X_train_full.shape[1],
        },
        "requirements": get_requirements(),
    }
    
    save_model_to_s3(model_data, os.getenv('S3_BUCKET'), f"models/{exp_name}")
    
    wandb.finish()
    print("🎉 완료!\n")
    
    return best_model, search.best_params_, cv_rmse


if __name__ == "__main__":
    fire.Fire(tune_hyperparameters)