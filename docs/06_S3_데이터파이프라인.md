# S3 Raw 데이터 적재 및 전처리 파이프라인 가이드

## 📋 개요

본 문서는 기상청(KMA) 원시 데이터를 S3에 적재하고 전처리하는 전체 파이프라인에 대한 상세 가이드입니다. 프로젝트의 데이터 처리 흐름을 완전히 이해하고 구현할 수 있도록 단계별로 설명합니다.

## 🔄 데이터 처리 방식

**실시간 전처리 방식**을 채택하고 있습니다:

```
KMA API 호출 → Raw 데이터 S3 저장 → [즉시 메모리에서 파싱] → Parsed 데이터 S3 저장 → ML 데이터셋 생성 및 저장
```

**장점:**
- ✅ **데이터 신선도**: API 호출 즉시 사용 가능한 ML 데이터셋 생성
- ✅ **메모리 효율성**: 대용량 Raw 데이터를 디스크에 저장하지 않고 스트리밍 처리
- ✅ **실시간 대응**: 매시간 최신 데이터로 모델 예측 가능
- ✅ **단순한 파이프라인**: 한 번의 워크플로우로 전체 처리 완료

## 🏗️ 시스템 아키텍처

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   KMA API   │ -> │  Raw Data   │ -> │ S3 Storage  │ -> │ML Dataset   │
│   (ASOS,    │    │  Parsing    │    │  (Raw +     │    │ Generation  │
│ PM10, UV)   │    │             │    │ Processed)  │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       |                   |                   |                   |
   매시간 수집         실시간 파싱         계층별 저장      ML 피처 생성
```

## 🔧 핵심 컴포넌트

### 1. KMA API 클라이언트 (`src/data/kma_client.py`)

기상청 API와의 통신을 담당하는 클라이언트입니다.

```python
from src.data.kma_client import KMAApiClient
from src.utils.config import KMAApiConfig

# 설정 로드
config = KMAApiConfig.from_env()
client = KMAApiClient(config)

# 데이터 수집
asos_data = client.fetch_asos()  # 지상 관측 데이터
pm10_data = client.fetch_pm10(start_time, end_time)  # 황사 데이터
uv_data = client.fetch_uv()  # 자외선 데이터
```

**주요 기능:**
- 시간 정규화 (정시 00분으로 강제 조정)
- API 요청 파라미터 자동 구성
- 에러 처리 및 로깅
- 전국 데이터 수집 지원 (station_id=0)

### 2. S3 스토리지 클라이언트 (`src/storage/s3_client.py`)

AWS S3 및 LocalStack 호환 스토리지 클라이언트입니다.

```python
from src.storage.s3_client import S3StorageClient, WeatherDataS3Handler

# S3 클라이언트 초기화
s3_client = S3StorageClient(
    bucket_name="weather-data-bucket",
    aws_access_key_id="your-access-key",
    aws_secret_access_key="your-secret-key",
    region_name="ap-northeast-2",
    endpoint_url="http://localhost:4566"  # LocalStack용 (선택사항)
)

# Weather 전용 핸들러
weather_handler = WeatherDataS3Handler(s3_client)
```

**스토리지 계층 구조:**
```
s3://weather-data-bucket/
├── raw/                    # 원시 데이터
│   ├── asos/2025/09/25/    # 지상 관측
│   ├── pm10/2025/09/25/    # 황사
│   └── uv/2025/09/25/      # 자외선
├── processed/              # 파싱된 데이터 (JSON)
│   ├── asos/2025/09/25/
│   ├── pm10/2025/09/25/
│   └── uv/2025/09/25/
└── ml_dataset/             # ML 훈련용 데이터셋
    └── 2025/09/25/
```

### 3. 기상 데이터 프로세서 (`src/data/weather_processor.py`)

원시 데이터 파싱부터 ML 데이터셋 생성까지 전체 처리를 담당합니다.

```python
from src.data.weather_processor import WeatherDataProcessor
from datetime import datetime

# 프로세서 초기화
processor = WeatherDataProcessor()

# 전체 파이프라인 실행
stored_keys = processor.process_and_store_weather_data(
    asos_raw=asos_raw_text,
    pm10_raw=pm10_raw_text,
    uv_raw=uv_raw_text,
    timestamp=datetime.now()
)

print(f"저장된 S3 객체: {stored_keys}")
```

## 📝 단계별 구현 가이드

### Step 1: 환경 설정

**.env 파일 구성:**
```bash
# KMA API 설정
KMA_API_KEY=your_api_key_here
KMA_BASE_URL=http://apis.data.go.kr/1360000/TourStnInfoService2/getTourStnVilageFcstMsgSvc
KMA_STATION_ID=0
KMA_TIMEOUT_SECONDS=30

# S3 설정
S3_BUCKET_NAME=weather-data-bucket
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=ap-northeast-2
S3_ENDPOINT_URL=  # 실제 AWS S3 사용 시 비워둠
```

### Step 2: 원시 데이터 수집

```python
from src.data.kma_client import KMAApiClient
from src.utils.config import KMAApiConfig
from datetime import datetime, timedelta

def collect_weather_data():
    """기상 데이터 수집"""

    # 설정 로드
    config = KMAApiConfig.from_env()
    client = KMAApiClient(config)

    # 1시간 전 데이터 수집 (최신 완전한 데이터)
    target_time = datetime.now() - timedelta(hours=1)

    # 각 데이터 타입별 수집
    try:
        print("🌤️ ASOS 데이터 수집 중...")
        asos_raw = client.fetch_asos(target_time)

        print("💨 PM10 데이터 수집 중...")
        pm10_raw = client.fetch_pm10(target_time, target_time)

        print("☀️ UV 데이터 수집 중...")
        uv_raw = client.fetch_uv(target_time)

        return {
            'asos': asos_raw,
            'pm10': pm10_raw,
            'uv': uv_raw,
            'timestamp': target_time
        }

    except Exception as e:
        print(f"❌ 데이터 수집 실패: {e}")
        return None
```

### Step 3: S3 저장 및 파싱

```python
from src.data.weather_processor import WeatherDataProcessor

def process_and_store_data(raw_data):
    """원시 데이터 처리 및 S3 저장"""

    # 프로세서 초기화
    processor = WeatherDataProcessor()

    # 전체 파이프라인 실행
    stored_keys = processor.process_and_store_weather_data(
        asos_raw=raw_data['asos'],
        pm10_raw=raw_data['pm10'],
        uv_raw=raw_data['uv'],
        timestamp=raw_data['timestamp']
    )

    if stored_keys:
        print("✅ S3 저장 완료:")
        for key_type, s3_key in stored_keys.items():
            print(f"  - {key_type}: {s3_key}")
    else:
        print("❌ S3 저장 실패")

    return stored_keys
```

### Step 4: ML 데이터셋 로드

```python
def load_latest_ml_dataset():
    """최신 ML 데이터셋 로드"""

    processor = WeatherDataProcessor()

    # 최근 7일 내 최신 데이터셋 로드
    df = processor.load_latest_ml_dataset(days_back=7)

    if df is not None:
        print(f"✅ ML 데이터셋 로드 완료:")
        print(f"  - 레코드 수: {len(df)}")
        print(f"  - 피처 수: {len(df.columns)}")
        print(f"  - 컬럼: {list(df.columns)}")

        # 쾌적지수 평균 출력
        if 'comfort_score' in df.columns:
            avg_comfort = df['comfort_score'].mean()
            print(f"  - 평균 쾌적지수: {avg_comfort:.1f}")

        return df
    else:
        print("❌ ML 데이터셋 로드 실패")
        return None
```

## 🚀 Airflow DAG 통합

프로덕션 환경에서는 Airflow를 통해 자동화된 파이프라인을 운영합니다.

### DAG 구조 (`dags/weather_data_pipeline.py`)

```python
# 매시간 10분에 실행
schedule_interval='10 * * * *'

# 태스크 플로우
start_task >> fetch_weather_task >> generate_ml_task >> validate_task >> end_task
```

**태스크별 역할:**

1. **fetch_weather_data**: KMA API에서 원시 데이터 수집 및 S3 저장
2. **generate_ml_dataset**: ML 피처 엔지니어링 및 데이터셋 생성
3. **validate_pipeline**: 파이프라인 성공 검증 및 데이터 무결성 확인

### 실행 결과 모니터링

```python
def validate_pipeline_success(**context):
    """파이프라인 검증"""

    # S3 데이터 인벤토리 확인
    inventory = weather_handler.get_data_inventory()
    print(f"S3 인벤토리: {inventory}")

    # 최신 ML 데이터셋 검증
    df = weather_handler.load_latest_ml_dataset()
    if df is not None and len(df) > 0:
        print(f"✅ 검증 완료: {len(df)} 레코드")
        return True
    else:
        raise ValueError("ML 데이터셋 검증 실패")
```

## 📊 데이터 스키마 및 품질

### 원시 데이터 포맷

**통합 기상 데이터 (weather_pm10_integrated_full.csv):**
```
YYMMDDHHMI,STN,WD,WS,GST,GST_2,GST_3,PA,PS,PT,PR,TA,TD,HM,PV,RN,RN_2,RN_3,RN_4,SD,SD_2,SD_3,WC,WP,WW,CA,CA_2,CH,CT,CT_2,CT_3,CT_4,VS,SS,SI,ST,TS,TE,TE_2,TE_3,TE_4,ST_2,WH,BF,IR,IX,datetime,PM10,PM10_FLAG
202401010900,100,9,0.8,-9,-9.0,-9,936.9,1031.7,2,1.1,-2.5,-3.3,94.0,4.8,0.0,0.0,0.0,-9.0,-9.0,-9.0,18.7,-9,-9,-,8,8,5,-,-9,-9,-9,1328,0.0,0.01,-9,-1.5,-99.0,-99.0,-99.0,-99.0,-9,-9.0,-9,3,-9,2024-01-01 09:00:00,15.0,000000
```
*포맷: 48개 컬럼의 쉼표 구분 CSV*
- **ASOS 기상 데이터**: 첫 45개 컬럼 (시간, 관측소ID, 풍향, 풍속, 기온, 습도, 기압 등)
- **PM10 데이터**: 마지막 2개 컬럼 (PM10, PM10_FLAG)

### ML 데이터셋 스키마

최종 ML 데이터셋은 **30개 피처**로 구성됩니다:

| 카테고리 | 피처 수 | 예시 |
|----------|---------|------|
| 기본 정보 | 2 | `station_id`, `datetime` |
| 원시 데이터 | 6 | `temperature`, `pm10`, `uv_*` |
| 시간 피처 | 8 | `hour`, `season`, `is_rush_hour` |
| 온도 피처 | 5 | `temp_category`, `temp_comfort` |
| 지역 피처 | 3 | `is_metro_area`, `region` |
| 대기질 피처 | 3 | `pm10_grade`, `mask_needed` |
| 자외선 피처 | 2 | `has_uv`, `sun_protection_needed` |
| 종합 지수 | 1 | `comfort_score` |

## 🔍 트러블슈팅

### 자주 발생하는 문제

**1. KMA API 인증 실패**
```bash
# 에러: Service key is not registered
# 해결: API 키 확인 및 갱신
export KMA_API_KEY=new_valid_key
```

**2. S3 연결 실패**
```python
# LocalStack 환경에서
S3_ENDPOINT_URL=http://localhost:4566

# AWS 실제 환경에서
S3_ENDPOINT_URL=  # 비워둠
```

**3. 데이터 파싱 오류**
```python
# 빈 응답 처리
if not raw_data or len(raw_data.strip()) == 0:
    logger.warning("Empty API response")
    return []
```

### 로그 모니터링

```python
from src.utils.logger_config import configure_logger

logger = configure_logger(__name__)
logger.info("파이프라인 시작")
logger.error(f"처리 실패: {error_message}")
```

## 🧪 테스트

### 통합 테스트

```python
def test_complete_pipeline():
    """전체 파이프라인 테스트"""

    # 1. 데이터 수집
    raw_data = collect_weather_data()
    assert raw_data is not None

    # 2. S3 저장
    stored_keys = process_and_store_data(raw_data)
    assert len(stored_keys) > 0

    # 3. ML 데이터셋 로드
    df = load_latest_ml_dataset()
    assert df is not None and len(df) > 0

    print("✅ 전체 파이프라인 테스트 통과")
```

### S3 연결 테스트

```python
def test_s3_connection():
    """S3 연결 테스트"""

    from src.storage.s3_client import S3StorageClient
    from src.utils.config import S3Config

    config = S3Config.from_env()
    client = S3StorageClient(
        bucket_name=config.bucket_name,
        aws_access_key_id=config.aws_access_key_id,
        aws_secret_access_key=config.aws_secret_access_key,
        region_name=config.region_name,
        endpoint_url=config.endpoint_url
    )

    # 테스트 객체 저장
    test_key = client.put_object("test/connection.txt", "connection test")

    # 테스트 객체 조회
    content = client.get_object(test_key)
    assert content.decode() == "connection test"

    # 테스트 객체 삭제
    client.delete_object(test_key)

    print("✅ S3 연결 테스트 통과")
```

## 📈 성능 최적화

### 배치 처리

```python
# 여러 시간대 데이터 일괄 처리
def batch_process_historical_data(start_date, end_date):
    """과거 데이터 일괄 처리"""

    processor = WeatherDataProcessor()
    current = start_date

    while current <= end_date:
        try:
            # 해당 시간 데이터 처리
            raw_data = collect_weather_data_for_time(current)
            stored_keys = processor.process_and_store_weather_data(
                **raw_data, timestamp=current
            )
            print(f"✅ {current} 처리 완료")

        except Exception as e:
            print(f"❌ {current} 처리 실패: {e}")

        current += timedelta(hours=1)
```

### 메모리 최적화

```python
# 대용량 데이터셋 처리 시 청크 단위로 처리
def process_large_dataset(df, chunk_size=10000):
    """대용량 데이터셋 청크 처리"""

    for i in range(0, len(df), chunk_size):
        chunk = df.iloc[i:i+chunk_size]

        # 청크별 처리
        processed_chunk = process_ml_features(chunk)

        # S3에 청크별 저장
        timestamp = datetime.now()
        chunk_key = f"ml_dataset/chunks/{timestamp.strftime('%Y%m%d_%H%M%S')}_{i}.parquet"

        # 청크 저장 로직
        save_chunk_to_s3(processed_chunk, chunk_key)
```

## 🔒 보안 고려사항

### 환경 변수 관리

```python
# 민감한 정보는 반드시 환경 변수로 관리
import os
from dotenv import load_dotenv

load_dotenv()

# 안전한 설정 로드
api_key = os.getenv('KMA_API_KEY')
if not api_key:
    raise ValueError("KMA_API_KEY 환경 변수가 설정되지 않았습니다")
```

### IAM 권한 설정

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::weather-data-bucket",
        "arn:aws:s3:::weather-data-bucket/*"
      ]
    }
  ]
}
```

## 📚 참고 자료

### 관련 문서
- [ML_DATASET_COLUMNS.md](./ML_DATASET_COLUMNS.md) - ML 데이터셋 컬럼 명세
- [PIPELINE_OVERVIEW.md](./PIPELINE_OVERVIEW.md) - 파이프라인 전체 개요

### API 문서
- [기상청 Open API](https://data.go.kr/data/15057682/openapi.do)
- [AWS S3 Python SDK](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)

### 모니터링 도구
- Airflow UI: `http://localhost:8080`
- S3 브라우저: AWS Console 또는 LocalStack Dashboard

---

**작성일**: 2025-09-25
**작성자**: MLOps Team
**버전**: 1.0.0