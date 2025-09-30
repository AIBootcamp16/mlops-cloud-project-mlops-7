# 팀 파이프라인 DAG 코드 참고서

Airflow DAG(`Airflow/dag/team_training_pipeline_dag.py`)가 호출하는 모듈과 함수들을 빠르게 익히기 위한 요약입니다. DAG가 실행하는 9단계의 원본 코드 위치, 주요 처리, 입력·출력, 주의사항을 정리했습니다.

## 1. 전체 플로우 개요

```
src/data/s3_pull.py               # ① Raw 데이터 S3에서 읽기
src/data/data_cleaning.py         # ② 전처리 & 파생 변수 생성
src/utils/utils.py (save_to_s3)   #     → 전처리 결과 S3 저장
src/data/s3_pull_processed.py     # ③ 처리된 데이터 재로딩
src/models/split.py               # ④ Train/Val/Test 분할 & 스케일링
src/models/train.py               # ⑤ 다중 모델 학습 + W&B 로깅 + 모델 S3 저장
src/models/tune.py                # ⑥ 하이퍼파라미터 튜닝 (항상 수행)
Airflow DAG champion task         # ⑦ 챔피언 승격(s3 copy)
src/utils/wandb_utils.py          #     W&B run 정보 유틸
src/config/hyperparams.yml        #     튜닝 파라미터 스페이스 정의
```

Airflow 태스크 순서: `step1_s3_pull_raw → step2_preprocess_and_save → step3_verify_processed_read → step4_split_dataset → step5_train_models → step6_tune_hyperparameters → step7_promote_champion`

## 2. 단계별 상세

### ① Raw 데이터 로드 — `src/data/s3_pull.py`
- **함수**: `get_s3_data()`
- **역할**: `S3_BUCKET` 환경변수로 지정된 버킷에서 `ml_dataset/past_data/weather_pm10_integrated_full.csv`를 읽어 `pandas.DataFrame` 반환.
- **의존성**: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`.

### ② 전처리 & 파생 — `src/data/data_cleaning.py`
- Airflow 태스크 `preprocess_and_save()`가 순서대로 호출.

| 함수 | 주요 처리 |
| --- | --- |
| `clean_weather_data(df)` | 컬럼명 정리, 필요한 컬럼만 유지, 타입 변환 |
| `add_time_features(df)` | datetime 기반 hour/day_of_week/season 등 파생 |
| `add_temp_features(df)` | 온도 구간, 극한 여부, 난방/냉방 필요 여부 |
| `add_air_quality_features(df)` | PM10 등급, 마스크 필요 여부 |
| `add_region_features(df)` | station_id 기반 권역/도시 플래그 |
| `add_comfort_score(df)` | 온도/미세먼지/출퇴근 여부를 종합한 comfort_score |

- **저장**: `src/utils/utils.py:save_to_s3(df, bucket, key)`로 `ml_dataset/weather_features_full.csv`에 업로드.

### ③ 처리 데이터 검증 — `src/data/s3_pull_processed.py`
- **함수**: `get_processed_data()`
- **역할**: 위에서 저장한 `ml_dataset/weather_features_full.csv`를 다시 읽어 shape 확인 및 다운스트림 일관성 유지.

### ④ Train/Val/Test 분할 — `src/models/split.py`
- **함수**: `split_and_scale_data(test_size=0.2, val_size=0.2, random_state=42)`
- **주요 로직**:
  - `get_processed_data()` 호출
  - 타깃: `comfort_score`
  - 제외 컬럼: `pm10`, `datetime`, `station_id` 등
  - 결측치 처리: -99/-9 → NaN → 평균값 대체, 결측 50% 이상 컬럼 삭제
  - 범주형: `season`, `temp_category`, `pm10_grade`, `region` 원핫 인코딩
  - `train_test_split` 두 번 → 6:2:2 분할, `StandardScaler` 적용
- **반환값**: `(X_train_scaled, X_val_scaled, X_test_scaled, y_train, y_val, y_test, scaler)`

### ⑤ 모델 학습 — `src/models/train.py`
- **함수**: `train_models(model_names, test_size, val_size, random_state, wandb_project)`
- **흐름**:
  1. `split_and_scale_data`로 데이터 확보
  2. `src.utils.model_utils.get_model()`로 모델 생성 (linear/ridge/lasso/rf/lgbm/xgb/cat 등)
  3. 각 모델 학습 → train/val/test RMSE·MAE 계산 → `wandb.log`
  4. Validation RMSE 최소 모델을 챔피언으로 선정
  5. `src.utils.utils.save_model_to_s3`로 모델·스케일러·메타데이터를 S3에 저장
- **W&B 관련**:
  - `WANDB_ENTITY`, `WANDB_PROJECT` 환경변수 사용
  - `src.utils.wandb_utils.get_latest_run_name()` + `auto_increment_run_suffix()`로 실험명 생성
  - DAG 기본 설정은 `WANDB_MODE=offline`; 온라인 로깅 원할 시 환경변수 및 `_set_env(..., wandb_offline=False)` 조정 필요

### ⑥ 하이퍼파라미터 튜닝 — `src/models/tune.py`
- **함수**: `tune_hyperparameters(model_name, search_type, cv_folds, n_iter, ...)`
- **주요 로직**:
  1. `split_and_scale_data` → train/val/test 확보, 학습용 `X_train_full = train + val`
  2. `src/config/hyperparams.yml`에서 모델별 파라미터 공간 로드
  3. `GridSearchCV` 또는 `RandomizedSearchCV` 실행, 각 조합의 CV 결과를 `wandb.log`
  4. 최적 모델 평가(Train/Test RMSE·MAE) 후 `save_model_to_s3` 사용해 S3 저장

### ⑦ 챔피언 승격 — `Airflow/dag/team_training_pipeline_dag.py`
- `step7_promote_champion` 태스크가 베이스라인/튜닝 결과의 `test_rmse`를 비교하여 더 우수한 모델을 선정합니다.
- 선정된 모델의 S3 경로(`models/<run_id>/...`) 전체를 `models/champion/<model_name>-<run_id>/...`으로 복사하고 `metadata/champion_info.json`을 생성합니다.

### ⑧ 유틸리티 & 설정
- `src/utils/utils.py`
  - `set_seed(seed)`: 난수 고정
  - `save_to_s3(df, bucket, key)`: DataFrame → CSV → S3 업로드
  - `save_model_to_s3(model_data, bucket, base_path)`: 모델, 스케일러, 메타데이터를 구조적으로 저장
  - `auto_increment_run_suffix(latest, default_prefix)`: 최신 실험명에서 suffix +1
- `src/utils/wandb_utils.py`
  - `get_latest_run_name(entity, project, prefix)`
  - `get_requirements()`: requirements.txt 내용 로드
- `src/config/hyperparams.yml`
  - 모델별 grid/random 파라미터 범위 정의 파일

## 3. Airflow DAG 구조 요약
- DAG ID: `team_weather_training_pipeline`
- 태스크 ↔ 함수 매핑:
  - `step1_s3_pull_raw` → `src/data/s3_pull.get_s3_data`
  - `step2_preprocess_and_save` → 전처리 함수 체인 + `save_to_s3`
  - `step3_verify_processed_read` → `src/data/s3_pull_processed.get_processed_data`
  - `step4_split_dataset` → `src/models.split.split_and_scale_data`
  - `step5_train_models` → `src/models.train.train_models`
  - `step6_tune_hyperparameters` (조건부) → `src/models.tune.tune_hyperparameters`
- Airflow Variables: `team_s3_bucket`, `team_dataset_prefix`, `team_wandb_api_key`, `team_wandb_entity`, `team_wandb_project`, `team_wandb_mode`.
- `_set_env()`에서 S3 버킷/Region 및 W&B 설정(`mode` 기본 online, 필요 시 `team_wandb_mode`로 변경)을 주입.

## 4. 활용 팁
- 각 함수는 독립 실행 가능 → `python -m src.models.train train_models --model_names='["rf"]'` 식으로 실험 가능.
- DAG 테스트: `airflow dags test team_weather_training_pipeline 2024-01-01`
- W&B 온라인 모드: 환경변수 추가(`WANDB_API_KEY`, `WANDB_ENTITY`, `WANDB_PROJECT`) 후 DAG 코드에서 `wandb_offline=False`로 조정.
- 실험명 규칙 변경: `WANDB_PROJECT` 값 또는 `auto_increment_run_suffix` 로직을 팀 규칙에 맞게 수정.

이 문서를 참고하며 실제 코드 파일을 따라가면 DAG 각 단계의 동작과 의존성을 체계적으로 이해할 수 있습니다.
