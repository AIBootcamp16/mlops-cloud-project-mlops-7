"""Team end-to-end training DAG wrapping teammates' pipeline steps.

This DAG orchestrates the following steps built by teammates (용재 외 팀원):
1) s3_pull.py: Load raw dataset from S3 (weather-mlops-team-data/ml_dataset/...)
2) data_cleaning.py: Preprocess/feature engineering
3) Save processed dataset to S3: ml_dataset/weather_features_full.csv
4) s3_pull_processed.py: Read processed dataset back from S3
5) split.py: Split (train/val/test = 6:2:2) + scaling
6) train.py: Train multiple models with W&B logging and save best model to S3
7) tune.py: Hyperparameter tuning (항상 수행)
8) Champion promotion: compare baseline vs tuned metrics, copy 최고 성능 모델을 `models/champion/...`에 저장

Notes:
- The tasks read/write S3 via environment variables. Configure S3_BUCKET in Airflow env/Variables.
- W&B 설정(team_wandb_*)을 입력하면 자동으로 온라인 로깅됩니다.
"""
from __future__ import annotations

import os
import json
from datetime import datetime

from airflow import DAG
from airflow.decorators import task
from airflow.models import Variable


def _set_env(bucket: str | None = None, *, wandb_settings: dict | None = None) -> None:
    if bucket:
        os.environ["S3_BUCKET"] = bucket
    if "AWS_REGION" not in os.environ:
        os.environ["AWS_REGION"] = os.environ.get("AWS_DEFAULT_REGION", "ap-northeast-2")

    wandb_settings = wandb_settings or {}
    mode = wandb_settings.get("mode") or os.environ.get("WANDB_MODE") or "online"
    os.environ["WANDB_MODE"] = mode

    api_key = wandb_settings.get("api_key")
    if api_key:
        os.environ["WANDB_API_KEY"] = api_key

    entity = wandb_settings.get("entity")
    if entity:
        os.environ["WANDB_ENTITY"] = entity

    project = wandb_settings.get("project")
    if project:
        os.environ["WANDB_PROJECT"] = project


default_args = {
    "owner": "mlops-team",
    "depends_on_past": False,
}


with DAG(
    dag_id="team_weather_training_pipeline",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["mlops", "training", "team"],
) as dag:
    # Airflow Variables (with sensible defaults for local)
    team_bucket = Variable.get("team_s3_bucket", default_var="weather-mlops-team-data")
    dataset_prefix = Variable.get("team_dataset_prefix", default_var="ml_dataset/")

    wandb_settings = {
        "api_key": Variable.get("team_wandb_api_key", default_var=None),
        "entity": Variable.get("team_wandb_entity", default_var=None),
        "project": Variable.get("team_wandb_project", default_var=None),
        "mode": Variable.get("team_wandb_mode", default_var="online"),
    }

    @task(task_id="step1_s3_pull_raw")
    def s3_pull_raw():
        """Load raw dataset from S3 and log basic info (no XCom payload)."""
        _set_env(bucket=team_bucket, wandb_settings=wandb_settings)
        from src.data import s3_pull

        df = s3_pull.get_s3_data()
        print("Raw DF shape:", getattr(df, "shape", None))
        # Avoid returning large data via XCom
        return {
            "bucket": team_bucket,
            "sample_columns": list(df.columns)[:10],
            "approx_rows": int(getattr(df, "shape", (0, 0))[0]),
        }

    @task(task_id="step2_preprocess_and_save")
    def preprocess_and_save():
        """Preprocess raw data then save processed CSV to S3."""
        _set_env(bucket=team_bucket, wandb_settings=wandb_settings)
        from src.data.s3_pull import get_s3_data
        from src.data import data_cleaning
        from src.utils.utils import save_to_s3

        raw_df = get_s3_data()
        df = data_cleaning.clean_weather_data(raw_df)
        df = data_cleaning.add_time_features(df)
        df = data_cleaning.add_temp_features(df)
        df = data_cleaning.add_air_quality_features(df)
        df = data_cleaning.add_region_features(df)
        df = data_cleaning.add_comfort_score(df)

        out_key = "ml_dataset/weather_features_full.csv"
        save_to_s3(df, bucket=team_bucket, key=out_key)
        return {"processed_key": out_key, "rows": int(df.shape[0]), "cols": int(df.shape[1])}

    @task(task_id="step3_verify_processed_read")
    def verify_processed():
        """Read processed dataset from S3 and log shape (sanity check)."""
        _set_env(bucket=team_bucket, wandb_settings=wandb_settings)
        from src.data.s3_pull_processed import get_processed_data

        df = get_processed_data()
        print("Processed DF shape:", df.shape)
        return {"rows": int(df.shape[0]), "cols": int(df.shape[1])}

    @task(task_id="step4_split_dataset")
    def split_dataset():
        """Split dataset into train/val/test and scale; return shapes only."""
        _set_env(bucket=team_bucket, wandb_settings=wandb_settings)
        from src.models.split import split_and_scale_data

        (
            X_tr,
            X_val,
            X_te,
            y_tr,
            y_val,
            y_te,
            _scaler,
            feature_columns,
        ) = split_and_scale_data(test_size=0.2, val_size=0.2)
        shapes = {
            "X_train": list(getattr(X_tr, "shape", (0, 0))),
            "X_val": list(getattr(X_val, "shape", (0, 0))),
            "X_test": list(getattr(X_te, "shape", (0, 0))),
            "y_train": int(len(y_tr)),
            "y_val": int(len(y_val)),
            "y_test": int(len(y_te)),
            "feature_count": len(feature_columns),
        }
        print("Split shapes:", shapes)
        return shapes

    @task(task_id="step5_train_models")
    def train_models_task():
        """Run training across multiple models; best model saved to S3 by utilities."""
        _set_env(bucket=team_bucket, wandb_settings=wandb_settings)
        from src.models.train import train_models

        result = train_models()
        print("Best model summary:", result.get("metrics"))
        return {"source": "baseline", **result}

    @task(task_id="step6_tune_hyperparameters")
    def tune_models_task():
        """Run hyperparameter tuning (Grid by default)."""
        _set_env(bucket=team_bucket, wandb_settings=wandb_settings)
        from src.models.tune import tune_hyperparameters

        # Using repo default config path; works with our volume layout
        result = tune_hyperparameters(
            model_name="rf",
            search_type="grid",
            config_path="/opt/airflow/src/config/hyperparams.yml",
        )
        print(
            "Tuning best params:",
            result.get("best_params"),
            "metrics:",
            result.get("metrics"),
        )
        return {"source": "tuned", **result}

    @task(task_id="step7_promote_champion")
    def promote_champion(train_result: dict, tune_result: dict):
        """Compare baseline/tuned metrics and copy the winner under models/champion."""

        _set_env(bucket=team_bucket, wandb_settings=wandb_settings)
        from src.utils.utils import get_s3_client

        candidates = []
        if train_result:
            candidates.append(train_result)
        if tune_result:
            candidates.append(tune_result)

        if not candidates:
            raise ValueError("No training results provided for champion promotion.")

        def extract_metric(record: dict) -> float:
            metrics = record.get("metrics", {})
            return float(metrics.get("test_rmse") or metrics.get("val_rmse") or metrics.get("cv_rmse") or float("inf"))

        best = min(candidates, key=extract_metric)
        runner_up = max(candidates, key=extract_metric)

        best_prefix = best["run_path"].rstrip("/")
        champion_prefix = f"models/champion/{best['model_name']}-{best['run_id']}".rstrip("/")

        client = get_s3_client()

        # Remove previous champion contents
        existing = client.list_objects_v2(Bucket=team_bucket, Prefix=champion_prefix)
        if existing.get("Contents"):
            client.delete_objects(
                Bucket=team_bucket,
                Delete={"Objects": [{"Key": obj["Key"]} for obj in existing["Contents"]]},
            )

        # Copy all artifacts from best run into champion prefix
        continuation = None
        while True:
            list_kwargs = {"Bucket": team_bucket, "Prefix": best_prefix}
            if continuation:
                list_kwargs["ContinuationToken"] = continuation
            response = client.list_objects_v2(**list_kwargs)
            for obj in response.get("Contents", []):
                key = obj["Key"]
                relative = key[len(best_prefix):].lstrip("/")
                dest_key = f"{champion_prefix}/{relative}" if relative else champion_prefix
                client.copy_object(CopySource={"Bucket": team_bucket, "Key": key}, Bucket=team_bucket, Key=dest_key)
            if response.get("IsTruncated"):
                continuation = response.get("NextContinuationToken")
            else:
                break

        # Write champion info metadata
        info = {
            "selected_source": best.get("source"),
            "selected_model": best.get("model_name"),
            "selected_run_id": best.get("run_id"),
            "selected_metrics": best.get("metrics"),
            "runner_up_source": runner_up.get("source"),
            "runner_up_model": runner_up.get("model_name"),
            "runner_up_run_id": runner_up.get("run_id"),
            "runner_up_metrics": runner_up.get("metrics"),
        }
        client.put_object(
            Bucket=team_bucket,
            Key=f"{champion_prefix}/metadata/champion_info.json",
            Body=json.dumps(info, indent=2, ensure_ascii=False).encode("utf-8"),
        )

        print("Champion updated:", json.dumps(info, indent=2, ensure_ascii=False))
        return {"champion_prefix": champion_prefix, "info": info}

    # Orchestration: keep the order aligned with the requested 9 steps (condensed)
    raw_info = s3_pull_raw()
    processed_info = preprocess_and_save()
    verify_info = verify_processed()
    split_info = split_dataset()
    train_info = train_models_task()
    tune_info = tune_models_task()
    champion_info = promote_champion(train_info, tune_info)

    raw_info >> processed_info >> verify_info >> split_info >> train_info >> tune_info >> champion_info
