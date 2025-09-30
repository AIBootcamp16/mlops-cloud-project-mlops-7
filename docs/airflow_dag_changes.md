# Airflow DAG 변경 요약

최근 `team_weather_training_pipeline` DAG을 실험/튜닝/챔피언 승격까지 자동화하도록 확장했습니다. 아래 내용은 팀원이 바로 이해하고 실행할 수 있도록 변경 사항과 실행 방법을 정리한 자료입니다.

## 1. 핵심 변경 사항
- **Airflow 스택 추가**: `docker-compose.yml`에 `airflow-postgres`, `airflow-init`, `airflow-webserver`, `airflow-scheduler` 서비스를 정의했고, 컨테이너 기동 시 `libgomp1`와 `requirements.txt`를 설치하도록 구성했습니다.
- **DAG 확장**: 기본 5단계 파이프라인에 튜닝(`step6_tune_hyperparameters`)을 항상 실행하도록 바꾸고, 베이스라인/튜닝 결과를 비교해 S3 `models/champion/<model>-<run>/...`에 복사하는 `step7_promote_champion`을 추가했습니다.
- **모델 반환 정보 수정**: `train_models()`와 `tune_hyperparameters()`가 S3 경로와 지표를 포함한 딕셔너리를 반환하도록 변경해 챔피언 승격 태스크에서 활용할 수 있게 했습니다.
- **CatBoost 오류 수정**: `logging_level` 사용으로 발생하던 충돌을 제거하고 `verbose=False`만 사용하도록 수정했습니다.
- **환경 변수 정리**: `.env`에서 `KMA_API_KEY`를 제거하고 `WEATHER_API_KEY`만 사용하도록 정리했습니다.

## 2. 새로 추가/변경된 파일 구조
```
Airflow/
└── dag/
    └── team_training_pipeline_dag.py

logs/
├── .gitkeep
└── … (Airflow 실행 시 생성되는 로그, 커밋 대상 아님)

plugins/
└── .gitkeep
```

## 3. 주요 코드 변경 요약
- `docker-compose.yml`
  - 공식 Airflow 이미지 사용, `libgomp1` 설치, `pip install -r requirements.txt` 후 Airflow 명령 실행.
  - Postgres 서비스, 공유 볼륨(`airflow-postgres-data`, `logs/`, `plugins/`) 추가.
- `src/models/train.py`
  - 학습 결과를 `{run_path, run_id, model_name, metrics, best_params}` 딕셔너리로 반환.
- `src/models/tune.py`
  - 튜닝 결과도 동일 구조로 반환, S3 저장 경로를 함께 제공.
- `src/utils/model_utils.py`
  - CatBoost 생성 시 `logging_level` 제거.
- `Airflow/dag/team_training_pipeline_dag.py`
  - 튜닝을 기본 실행, 승격 태스크 추가, XCom 구조 업데이트.
- `docs/team_dag_code_reference.md`, `docs/work_log.md`
  - DAG 단계와 환경 변수, 작업 이력을 최신 구조에 맞게 갱신.

## 4. 실행 절차 (로컬)
1. `.env`에 S3/AWS/W&B/WEATHER 설정이 있는지 확인 (`WANDB_*`, `S3_BUCKET`, `WEATHER_API_KEY` 등).
2. 로그/플러그인 디렉터리 준비
   ```bash
   mkdir -p logs/webserver logs/scheduler plugins
   chmod -R 777 logs plugins
   ```
3. Airflow 기동
   ```bash
   docker compose run --rm airflow-init
   docker compose up -d airflow-webserver airflow-scheduler
   ```
4. Airflow UI (`http://localhost:8080`, admin/admin) 접속 → Admin → Variables에 아래 값 입력
   - `team_s3_bucket`, `team_dataset_prefix`
   - `team_wandb_api_key`, `team_wandb_entity`, `team_wandb_project`, `team_wandb_mode=online`
5. DAG 실행
   - UI: `team_weather_training_pipeline` 토글 → “Trigger DAG”
   - CLI: `docker compose exec --user airflow airflow-webserver airflow dags trigger team_weather_training_pipeline`
6. 실행 후 검증
   - W&B: `weather-predictor-XXX`, `rf-tune-XXX` Run 로그
   - S3: `models/<run>/...`, `models/champion/<model>-<run>/...` 생성

## 5. 현재 상태
- CLI 기반 테스트에서 `step1`~`step7`이 모두 성공(`airflow dags state ... = success`)했습니다.
- 챔피언 승격 결과는 `metadata/champion_info.json`에 기록되어 있어 모델 선택 근거를 추적할 수 있습니다.

이 문서를 참고하면 다른 팀원도 동일 환경에서 DAG을 실행하고 결과를 확인할 수 있습니다.
