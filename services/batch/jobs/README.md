# Weather Batch Jobs Reference

이 폴더는 Airflow 배치 DAG에서 재사용되는 도메인 로직을 한곳에 모아 둔 패키지입니다. 현재 두 개의 DAG가 이 모듈을 공유합니다.

| DAG ID | 파일 | 주요 기능 |
| --- | --- | --- |
| `weather_data_pipeline` | `services/batch/dags/weather_data_pipeline.py` | KMA API에서 시간당 기상자료(ASOS, PM10, UV)를 수집하고, S3에 raw/parsed/ML 데이터를 적재하며, 필요 시 마스터 CSV를 최신화 |
| `master_data_rolling_window_weekly` | `services/batch/dags/master_data_update_dag.py` | 주 1회 마스터 데이터셋을 Rolling Window(630일) 규칙으로 정리하고 검증 |

두 DAG 모두 아래 `jobs/` 패키지에 있는 로직을 공유합니다.

## 디렉터리 개요

```
services/batch/jobs
├── __init__.py
├── data
│   ├── __init__.py
│   ├── kma_client.py
│   ├── parsers.py
│   └── weather_processor.py
├── features
│   ├── __init__.py
│   └── feature_builder.py
└── storage
    ├── __init__.py
    └── s3_client.py
```

### data/
- **kma_client.py**: 기상청(KMA) API 호출 래퍼. `fetch_asos`, `fetch_pm10`로 시간대별 텍스트 데이터를 가져옵니다. `weather_data_pipeline`의 `fetch_kma_weather_data` 태스크에서 사용됩니다.
- **parsers.py**: KMA 응답을 구조화된 레코드 목록으로 변환하는 유틸리티. `weather_processor` 내부에서 호출됩니다.
- **weather_processor.py**: KMA 데이터 다운로드→파싱→S3 저장→ML/마스터 데이터셋 생성까지 담당하는 고수준 서비스. 두 DAG 모두 이 모듈을 통해 동일한 비즈니스 로직을 공유합니다.

### features/
- **feature_builder.py**: ASOS/PM10 데이터를 학습/추론용 DataFrame으로 변환. `create_ml_dataset(..., include_labels=True/False)`를 제공하며, 실시간 추론(`weather_data_pipeline`)과 Rolling Window 후 학습용 재생성(`master_data_update_dag`)에 함께 사용됩니다.

### storage/
- **s3_client.py**: S3 접근 래퍼(`S3StorageClient`)와 날씨 데이터 전용 헬퍼(`WeatherDataS3Handler`)를 제공합니다. raw/parsed/ML/CSV 저장 및 로딩을 처리하며, 두 DAG 모두 동일한 인터페이스를 사용합니다.

## DAG에서 사용하는 방법
```python
from jobs.data.weather_processor import WeatherDataProcessor
from jobs.features.feature_builder import create_ml_dataset
from jobs.storage.s3_client import S3StorageClient, WeatherDataS3Handler
from src.utils.config import S3Config
```
- DAG 파일 상단에서 `jobs`와 프로젝트 `src` 경로를 `sys.path`에 추가합니다.
- `src/utils/...` 모듈은 공용이므로 그대로 `src`에서 임포트합니다.

## 참고 문서
- `docs/team_dag_code_reference.md`: 팀 DAG 흐름과 모듈 의존성 요약.
- `docs/yongjae_log_2025-10-01.md`: DAG 정리 및 파일 이동 작업 이력.

이 README만으로도 각 DAG가 어떤 코드와 쌍을 이루는지 파악할 수 있도록 구성했습니다.
