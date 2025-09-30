# 작업 기록

본 문서는 `origin/main2` 기준(HEAD: fff01ae)에서 로컬로 수행한 변경 사항과 팀 공유가 필요한 메모를 정리합니다. 날짜는 KST 기준입니다.

## 2025-09-27 (Sat)
- 최상위 `dag/` 디렉터리를 `Airflow/`로, 내부 `Airflow/airflow/`를 `Airflow/dag/`로 통합해 DAG 경로를 정리했습니다.
- 중복되던 상위 `airflow/` 디렉터리를 제거해 동일 DAG가 두 번 존재하지 않도록 정리했습니다.
- `docs/pipeline_overview.md`에 명시된 DAG 경로를 새 구조(`Airflow/dag/weather_training_dag.py`)에 맞춰 수정했습니다.
- Airflow를 로컬 Docker Compose 스택(Postgres + init + webserver + scheduler)으로 띄울 수 있도록 `docker-compose.yml`과 `dockerfiles/Dockerfile.airflow`를 추가/수정했습니다.
- Airflow 컨테이너가 DAG/소스/로그/플러그인 디렉터리에 접근할 수 있도록 볼륨 및 빈 디렉터리(`logs/.gitkeep`, `plugins/.gitkeep`)를 준비했습니다.

## 2025-09-28 (Sun)

### 변경 파일 트리 (main2 pull 이후 추가/수정)
```
Airflow/
└── dag/
    └── team_training_pipeline_dag.py    # 팀 파이프라인 DAG (신규)
```

### 주요 변경 사항
- **팀 파이프라인 DAG**: `Airflow/dag/team_training_pipeline_dag.py`
  - 팀원 코드 9단계를 순차 태스크로 감싸는 DAG(`team_weather_training_pipeline`) 신규 작성.
  - 단계 요약: S3 raw 로드 → 전처리/파생 → processed CSV S3 저장 → processed 재검증 → split(6:2:2) → 다중 모델 학습(W&B 로그, S3 저장) → RF 튜닝 → 챔피언 승격(S3 `models/champion/...`).
  - Airflow Variables: `team_s3_bucket`(기본 `weather-mlops-team-data`), `team_dataset_prefix`(향후 논의를 위해 기본 `ml_dataset/`).
  - Airflow Variables에 W&B 설정을 입력하면 온라인으로 자동 로깅.
- **문서 정리**: 충돌 분석 리포트(`docs/conflict_analysis/conflict-test_vs_main2.md`)는 `conflict-test` 브랜치에서만 유지하도록 main2에서는 제거.
- **학습 자료**: DAG에 사용되는 모든 모듈·함수를 한눈에 정리한 `docs/team_dag_code_reference.md` 생성.
- **W&B 연동 개선**: DAG `_set_env`가 Airflow Variables(`team_wandb_api_key`, `team_wandb_entity`, `team_wandb_project`, `team_wandb_mode`)를 읽어 기본 온라인 모드로 로깅하도록 수정.
- **환경 변수 정리**: `.env`에 `S3_BUCKET`, `WANDB_API_KEY`, `WANDB_ENTITY`, `WANDB_PROJECT`, `WANDB_MODE`를 추가해 Airflow/Docker Compose에서 동일 값을 사용하도록 정리.
- **Airflow 스택 추가**: `docker-compose.yml`에 `airflow-postgres`, `airflow-init`, `airflow-webserver`, `airflow-scheduler` 서비스를 정의하고 `airflow-postgres-data` 볼륨, `logs/`, `plugins/` 디렉터리를 준비했습니다. (맞춤 Dockerfile 대신 `apache/airflow:2.8.4-python3.11` 이미지를 이용하며 컨테이너 시작 시 `requirements.txt`를 설치하도록 구성)
- **Weather API 키 정리**: `.env`에서 `KMA_API_KEY`를 제거하고 `WEATHER_API_KEY`를 사용하는 환경 변수로 통일했습니다.
- **DAG 개선**: 튜닝 태스크를 기본 수행하도록 변경하고, 베이스라인/튜닝 결과를 비교해 성능이 더 좋은 모델을 `models/champion/<model>-<run>`에 복사하는 `step7_promote_champion`을 추가했습니다.

### 팀 논의 필요 항목
1. `team_dataset_prefix` 활용 방식: 현재 DAG에서는 기본값만 지정(미사용). 향후 S3 경로 규칙을 어떻게 잡을지 논의 필요.
2. W&B 로깅 방식:
   - 환경 변수(`WANDB_API_KEY`, `WANDB_ENTITY`, `WANDB_PROJECT`, `WANDB_MODE`)를 어떤 값으로 공유할지 합의.
   - 실험명 접두사 규칙(예: `[Name]_001` 형태) 확정 → `train.py`의 `wandb_project`/`auto_increment_run_suffix` 활용 방안 조율.
3. 충돌 분석 문서: 실사용 브랜치(conflict-test)에만 두기로 했으므로, 공유 시 해당 브랜치 위치를 안내.

### 참고
- Airflow UI 실행: `docker compose up -d airflow-webserver airflow-scheduler` 후 `http://localhost:8080` (admin/admin).
- 작업 중 추가한 새로운 파일/디렉터리는 아직 Git에 커밋되지 않았습니다(`Airflow/` 디렉터리 등). 팀과 결정 후 `git add` 여부를 정하십시오.
