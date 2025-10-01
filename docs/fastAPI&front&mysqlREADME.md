# 🌤️ FastAPI + Frontend + MySQL 통합 아키텍처

> **출퇴근길 날씨 친구** - 실시간 쾌적지수 예측 서비스  
> FastAPI 백엔드, Next.js 프론트엔드, MySQL 캐싱을 활용한 MLOps 프로젝트

---

## 📋 목차

1. [전체 아키텍처](#-전체-아키텍처)
2. [FastAPI 백엔드](#-fastapi-백엔드)
3. [Next.js 프론트엔드](#-nextjs-프론트엔드)
4. [MySQL 캐싱 전략](#-mysql-캐싱-전략)
5. [배치 예측 파이프라인](#-배치-예측-파이프라인)
6. [API 엔드포인트 상세](#-api-엔드포인트-상세)
7. [데이터 플로우](#-데이터-플로우)
8. [실행 방법](#-실행-방법)
9. [환경 변수](#-환경-변수)
10. [트러블슈팅](#-트러블슈팅)

---

## 🏗️ 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    사용자 (브라우저)                          │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP Request
                     ▼
┌─────────────────────────────────────────────────────────────┐
│          Next.js Frontend (Port 3000)                        │
│  ┌──────────────────────────────────────────────────┐       │
│  │  - index.js: UI/UX 렌더링                         │       │
│  │  - API 호출: /api/welcome, /predict/*            │       │
│  │  - Chart.js: 원형 게이지 시각화                  │       │
│  └──────────────────────────────────────────────────┘       │
└────────────────────┬────────────────────────────────────────┘
                     │ API Request (localhost:8000)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│          FastAPI Backend (Port 8000)                         │
│  ┌──────────────────────────────────────────────────┐       │
│  │  api/main.py                                      │       │
│  │  - GET /                   : API 정보             │       │
│  │  - GET /health            : 헬스체크             │       │
│  │  - GET /predict/{type}    : 쾌적지수 예측        │       │
│  │  - GET /api/welcome       : 환영 메시지          │       │
│  └──────────────┬───────────────────────────────────┘       │
│                 │                                             │
│                 ├─→ 1️⃣ MySQL 캐시 확인 (mysql_client.py)   │
│                 │     └─ HIT: 저장된 데이터 반환             │
│                 │     └─ MISS: 2️⃣로 이동                    │
│                 │                                             │
│                 └─→ 2️⃣ ML 모델 예측 (batch_predict.py)     │
│                       ├─ S3에서 최신 데이터 로드             │
│                       ├─ S3에서 모델 로드                    │
│                       ├─ 전처리 + 예측                       │
│                       └─ MySQL에 저장                        │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴──────────────┐
        ▼                           ▼
┌─────────────────┐         ┌─────────────────┐
│  MySQL (3306)   │         │  AWS S3         │
│  - 예측 캐싱     │         │  - ML 데이터     │
│  - 1시간 단위    │         │  - 학습 모델     │
│  - station_id    │         │  - 스케일러      │
└─────────────────┘         └─────────────────┘
```

---

## 🚀 FastAPI 백엔드

### 📁 파일: `api/main.py`

#### **주요 기능**

1. **쾌적지수 예측 API** (캐시 우선)
2. **시간대별 환영 메시지**
3. **CORS 설정** (프론트엔드 연동)
CORS (Cross-Origin Resource Sharing) = 다른 출처 간 자원 공유
웹 브라우저의 보안 정책
4. **MySQL 캐싱 메커니즘**

#### **핵심 로직**

```python
@app.get("/predict/{prediction_type}")
def get_comfort_score(prediction_type: str):
    """
    쾌적지수 예측 (캐시 우선 조회)
    
    Flow:
    1. 현재 시간을 정각 기준으로 맞춤 (KST)
    2. MySQL에서 캐시 조회
       - HIT: 저장된 데이터 즉시 반환
       - MISS: ML 모델 예측 → MySQL 저장 → 반환
    3. 점수별 평가 레이블 생성 (excellent/good/fair/poor)
    """
```

#### **CORS 설정**

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 💻 Next.js 프론트엔드

### 📁 파일: `frontend/pages/index.js`

#### **주요 기능**

1. **실시간 API 연동**
2. **Chart.js 원형 게이지**
3. **반응형 디자인**
4. **환영 메시지 동적 로딩**

#### **API 연동 구조**

```javascript
// API 기본 URL 설정
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// 1️⃣ 환영 메시지 가져오기 (컴포넌트 마운트 시)
useEffect(() => {
  const fetchWelcomeMessage = async () => {
    const response = await fetch(`${API_BASE_URL}/api/welcome`);
    const data = await response.json();
    setWelcomeMessage(data.message);
  };
  fetchWelcomeMessage();
}, []);

// 2️⃣ 쾌적지수 예측 (버튼 클릭 시)
const getPrediction = async (type) => {
  const response = await fetch(`${API_BASE_URL}/predict/${type}`);
  const data = await response.json();
  setResult(data);
};
```

#### **버튼 매핑**

| 버튼 | API 호출 | 설명 |
|------|----------|------|
| 📱 지금 날씨 | `/predict/now` | 현재 시각 예측 |
| 🌅 출근길 예측 | `/predict/morning` | 6-9시 예측 |
| 🌆 퇴근길 예측 | `/predict/evening` | 18-21시 예측 |

---

## 🗄️ MySQL 캐싱 전략

### 📁 파일: `src/storage/mysql_client.py`

#### **캐싱 목적**

1. **ML 모델 추론 비용 절감** (S3 I/O, 연산 비용)
2. **응답 속도 개선** (캐시 HIT: ~50ms, ML 예측: ~3-5초)
3. **동일 시간대 중복 예측 방지**

#### **테이블 구조**

```sql
CREATE TABLE weather_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    comfort_score FLOAT,              -- 쾌적지수 (0-100)
    temperature FLOAT,                -- 온도 (°C)
    humidity FLOAT,                   -- 습도 (%)
    rainfall FLOAT,                   -- 강수량 (mm)
    pm10 FLOAT,                       -- 미세먼지 (㎍/㎥)
    wind_speed FLOAT,                 -- 풍속 (m/s)
    pressure FLOAT,                   -- 기압 (hPa)
    prediction_datetime DATETIME,     -- 예측 시간 (정각)
    region VARCHAR(50),               -- 지역명
    station_id VARCHAR(10),           -- 관측소 ID (기본: 108)
    model_name VARCHAR(100),          -- 모델명
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_prediction (prediction_datetime, station_id)
);
```

#### **핵심 함수**

##### 1️⃣ `query_prediction_by_datetime()`

```python
def query_prediction_by_datetime(prediction_datetime: datetime, station_id: str = '108'):
    """
    특정 시간대 예측 결과 조회
    
    Args:
        prediction_datetime: 정각 단위 시간 (예: 2025-10-01 14:00:00)
        station_id: 관측소 ID (기본: 108 = 서울)
    
    Returns:
        dict: 캐시된 예측 결과 또는 None
    """
```

##### 2️⃣ `save_prediction_to_mysql()`

```python
def save_prediction_to_mysql(result_df: pd.DataFrame, prediction_datetime: datetime):
    """
    예측 결과를 MySQL에 저장 (UPSERT)
    
    UPSERT 로직:
    - 동일 (prediction_datetime, station_id) 존재 시 → UPDATE
    - 없으면 → INSERT
    
    장점:
    - 중복 데이터 방지
    - 재예측 시 기존 데이터 갱신
    """
```

#### **캐싱 플로우**

```python
# api/main.py 내부
current_hour = datetime.now(kst).replace(minute=0, second=0, microsecond=0)
cached = query_prediction_by_datetime(current_hour)

if cached:
    # ✅ 캐시 HIT: 즉시 반환
    comfort_score = cached['comfort_score']
    weather_data = {...}
else:
    # ❌ 캐시 MISS: ML 모델 예측
    result_df = batch_predict(experiment_name='weather-predictor-018')
    save_prediction_to_mysql(result_df, current_hour)
    comfort_score = result_df['predicted_comfort_score']
```

---

## 🤖 배치 예측 파이프라인

### 📁 파일: `src/models/batch_predict.py`

#### **주요 단계**

```
1️⃣ S3에서 최신 parquet 로드
   └─ get_latest_parquet_from_s3()
   └─ ml_dataset/ 경로에서 최신 날짜 폴더 탐색

2️⃣ 시간대 변환 (UTC → KST)
   └─ pytz.timezone('Asia/Seoul')

3️⃣ S3에서 모델 아티팩트 로드
   └─ load_model_from_s3()
   └─ model.pkl, scaler.pkl, config.json, feature_columns.json

4️⃣ 전처리 (split.py 로직 동일)
   └─ preprocess_for_prediction()
   └─ 카테고리 통일, 결측치 처리, 원핫인코딩

5️⃣ ML 모델 예측
   └─ model.predict(X_scaled)

6️⃣ 결과 반환
   └─ DataFrame (datetime, station_id, comfort_score, 기상 데이터)
```

#### **핵심 함수**

##### 1️⃣ `get_latest_parquet_from_s3()`

```python
def get_latest_parquet_from_s3(bucket: str = None):
    """
    S3에서 최신 parquet 파일 자동 로드
    
    로직:
    1. ml_dataset/ 경로의 모든 parquet 파일 목록 조회
    2. LastModified 기준 정렬
    3. 최신 파일 선택 및 로드
    
    장점:
    - 항상 최신 데이터로 예측
    - 수동 경로 지정 불필요
    """
```

##### 2️⃣ `load_model_from_s3()`

```python
def load_model_from_s3(experiment_name: str, bucket: str = None):
    """
    S3에서 모델, 스케일러, config, feature_columns 로드
    
    로드 파일:
    - models/{experiment_name}/model_artifact/model.pkl
    - models/{experiment_name}/model_artifact/scaler.pkl
    - models/{experiment_name}/config/train_config.json
    - models/{experiment_name}/config/feature_columns.json
    
    반환:
    - model: 학습된 ML 모델
    - scaler: StandardScaler 객체
    - config: 학습 설정
    - feature_columns: 학습 시 사용된 컬럼 순서
    """
```

##### 3️⃣ `preprocess_for_prediction()`

```python
def preprocess_for_prediction(df, feature_columns):
    """
    split.py와 동일한 전처리 로직 + 컬럼 맞추기
    
    단계:
    1. 카테고리 이름 통일 (unhealthy→bad, very_unhealthy→very_bad)
    2. 타겟 컬럼 제외
    3. 결측치(-99, -9) → NaN 변환
    4. 고결측 컬럼 제거 (50% 이상)
    5. 결측치 평균 대체
    6. 원핫인코딩 (season, temp_category, pm10_grade, region)
    7. 학습 시 컬럼에 맞춰 보정 (없는 컬럼 0으로 채우기)
    
    중요:
    - 학습 시 컬럼 순서와 동일하게 맞춰야 함!
    - feature_columns 순서대로 재정렬
    """
```

##### 4️⃣ `batch_predict()`

```python
def batch_predict(experiment_name: str = None, output_path: str = None):
    """
    배치 추론 실행 (S3 최신 데이터 자동 로드)
    
    Args:
        experiment_name: 모델명 (기본: 'weather-predictor-018')
        output_path: 결과 CSV 저장 경로 (옵션)
    
    Returns:
        result_df: 예측 결과 DataFrame
            - datetime: 예측 시간 (KST)
            - station_id: 관측소 ID
            - predicted_comfort_score: 예측된 쾌적지수
            - temperature, humidity, rainfall, pm10, wind_speed, pressure, region
    
    예시:
        result_df = batch_predict(experiment_name='weather-predictor-018')
    """
```

---

## 📡 API 엔드포인트 상세

### **1️⃣ GET /**

```http
GET http://localhost:8000/
```

**응답:**
```json
{
  "message": "Weather Comfort Score API v0.1.0 실행 중!",
  "description": "batch_predict.py 기반 쾌적지수 예측 API",
  "endpoints": ["/predict/now", "/predict/morning", "/predict/evening", "/health"]
}
```

**사용처:** API 정보 확인 (프론트엔드 미사용)

---

### **2️⃣ GET /health**

```http
GET http://localhost:8000/health
```

**응답:**
```json
{
  "status": "healthy",
  "api_version": "0.1.0"
}
```

**사용처:** 헬스체크, 모니터링 (프론트엔드 미사용)

---

### **3️⃣ GET /predict/{prediction_type}**

```http
GET http://localhost:8000/predict/now
GET http://localhost:8000/predict/morning
GET http://localhost:8000/predict/evening
```

**파라미터:**
- `prediction_type`: `now` | `morning` | `evening`

**응답 예시:**
```json
{
  "title": "📱 현재 시점 예측",
  "score": 75.3,
  "label": "good",
  "evaluation": "쾌적한 날씨입니다! 😊",
  "prediction_time": "2025-10-01 14:00",
  "weather_data": {
    "temperature": 22.5,
    "humidity": 65,
    "rainfall": 0,
    "pm10": 45,
    "wind_speed": 2.3,
    "pressure": 1013,
    "region": "서울",
    "station_id": "108"
  },
  "prediction_type": "now",
  "status": "success"
}
```

**점수 평가 기준:**

| 점수 범위 | label | evaluation | 색상 |
|----------|-------|------------|------|
| 80-100 | excellent | 완벽한 날씨입니다! 🌟 | #FFB300 (골드) |
| 60-79 | good | 쾌적한 날씨입니다! 😊 | #43A047 (그린) |
| 40-59 | fair | 보통 날씨입니다 😐 | #FB8C00 (오렌지) |
| 0-39 | poor | 날씨가 좋지 않습니다 ⚠️ | #E53935 (레드) |

**캐싱 동작:**
- **캐시 HIT**: MySQL에 저장된 데이터 반환 (~50ms)
- **캐시 MISS**: ML 모델 예측 후 MySQL 저장 (~3-5초)

**사용처:** 프론트엔드 메인 기능 (버튼 클릭 시)

---

### **4️⃣ GET /api/welcome**

```http
GET http://localhost:8000/api/welcome
```

**응답 예시:**
```json
{
  "message": "좋은 아침이에요! 😊<br>오늘 하루도 화이팅입니다! ☀️",
  "current_time": "2025-10-01 08:30",
  "hour": 8
}
```

**시간대별 메시지:**

| 시간 | 메시지 |
|------|--------|
| 05:00-08:59 | 좋은 아침이에요! 😊<br>오늘 하루도 화이팅입니다! ☀️ |
| 09:00-11:59 | 활기찬 오전이네요! 💪<br>오늘도 좋은 하루 되세요! ✨ |
| 12:00-13:59 | 점심시간이에요! 🍽️<br>맛있는 식사 하시고 힘내세요! 😋 |
| 14:00-17:59 | 근무하시느라 힘드시죠? 💼<br>조금만 더 힘내세요! 응원합니다! 📈 |
| 18:00-21:59 | 오늘도 고생 많으셨어요! 😊<br>푹 쉬시고 좋은 저녁 되세요! 🌆 |
| 22:00-04:59 | 늦은 시간이네요! 🌙<br>푹 쉬시고 내일도 좋은 하루 되세요! 💤 |

**사용처:** 프론트엔드 초기 화면 (환영 메시지)

---

## 🔄 데이터 플로우

### **시나리오 1: 캐시 HIT (빠른 응답)**

```
[사용자] 
    └─> 버튼 클릭: "지금 날씨"
         │
         ▼
[Frontend] 
    └─> GET /predict/now
         │
         ▼
[FastAPI]
    └─> 현재 시간: 2025-10-01 14:00
         │
         ▼
[MySQL 조회]
    └─> SELECT * WHERE prediction_datetime='2025-10-01 14:00' AND station_id='108'
         │
         ├─✅ 데이터 존재
         │   │
         │   ▼
         └─> 즉시 반환 (comfort_score: 75.3, temperature: 22.5, ...)
              │
              ▼
[Frontend]
    └─> 원형 게이지 렌더링
         └─> 날씨 정보 표시
```

**소요 시간:** ~50-100ms

---

### **시나리오 2: 캐시 MISS (ML 예측)**

```
[사용자] 
    └─> 버튼 클릭: "출근길 예측"
         │
         ▼
[Frontend] 
    └─> GET /predict/morning
         │
         ▼
[FastAPI]
    └─> 현재 시간: 2025-10-01 09:00
         │
         ▼
[MySQL 조회]
    └─> SELECT * WHERE prediction_datetime='2025-10-01 09:00' AND station_id='108'
         │
         ├─❌ 데이터 없음
         │   │
         │   ▼
         └─> batch_predict() 호출
              │
              ▼
[Batch Predict]
    ├─> 1️⃣ S3에서 최신 parquet 로드
    │    └─ ml_dataset/2025/10/01/weather_features_20251001.parquet
    │
    ├─> 2️⃣ S3에서 모델 로드
    │    └─ models/weather-predictor-018/model_artifact/model.pkl
    │
    ├─> 3️⃣ 전처리
    │    └─ 카테고리 통일, 결측치 처리, 원핫인코딩, 스케일링
    │
    ├─> 4️⃣ ML 예측
    │    └─ model.predict() → comfort_score: 82.1
    │
    └─> 5️⃣ 결과 반환
         │
         ▼
[MySQL 저장]
    └─> INSERT INTO weather_predictions (comfort_score, temperature, ..., prediction_datetime, ...)
         │
         ▼
[FastAPI]
    └─> 결과 JSON 생성 후 반환
         │
         ▼
[Frontend]
    └─> 원형 게이지 렌더링
         └─> 날씨 정보 표시
```

**소요 시간:** ~3-5초 (최초 1회, 이후 캐시 사용)

---

## 🚀 실행 방법

### **1️⃣ 환경 변수 설정**

```bash
# .env 파일 생성
cat > .env << EOF
# AWS S3
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET=your_bucket_name

# MySQL
MYSQL_HOST=mysql
MYSQL_ROOT_PASSWORD=mlops2025
MYSQL_DATABASE=weather_mlops

# API
DEFAULT_MODEL_NAME=weather-predictor-018
EOF
```

### **2️⃣ Docker Compose 실행**

```bash
# 전체 서비스 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f api-server
docker-compose logs -f frontend
```

### **3️⃣ 서비스 접속**

| 서비스 | URL | 설명 |
|--------|-----|------|
| 프론트엔드 | http://localhost:3000 | Next.js 웹 UI |
| FastAPI 문서 | http://localhost:8000/docs | Swagger UI |
| MySQL | localhost:3307 | phpMyAdmin: http://localhost:8080 |

### **4️⃣ 수동 테스트**

```bash
# 1. 환영 메시지 조회
curl http://localhost:8000/api/welcome

# 2. 현재 날씨 예측
curl http://localhost:8000/predict/now

# 3. 헬스체크
curl http://localhost:8000/health

# 4. API 정보
curl http://localhost:8000/
```

---

## 🔧 환경 변수

### **백엔드 (api-server)**

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `AWS_ACCESS_KEY_ID` | - | AWS 액세스 키 |
| `AWS_SECRET_ACCESS_KEY` | - | AWS 시크릿 키 |
| `S3_BUCKET` | - | S3 버킷 이름 |
| `MYSQL_HOST` | `mysql` | MySQL 호스트 |
| `MYSQL_ROOT_PASSWORD` | `mlops2025` | MySQL 루트 비밀번호 |
| `MYSQL_DATABASE` | `weather_mlops` | 데이터베이스 이름 |
| `DEFAULT_MODEL_NAME` | `weather-predictor-018` | 기본 모델명 |

### **프론트엔드 (frontend)**

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | FastAPI 백엔드 URL |

---

## 🔍 트러블슈팅

### **1️⃣ CORS 오류**

```
Access to fetch at 'http://localhost:8000/predict/now' from origin 'http://localhost:3000' 
has been blocked by CORS policy
```

**해결:**
```python
# api/main.py에서 CORS origins 확인
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # ← 포트 확인
    ...
)
```

---

### **2️⃣ MySQL 연결 실패**

```
pymysql.err.OperationalError: (2003, "Can't connect to MySQL server")
```

**해결:**
```bash
# MySQL 컨테이너 상태 확인
docker-compose ps mysql

# MySQL 로그 확인
docker-compose logs mysql

# 환경 변수 확인
echo $MYSQL_HOST
echo $MYSQL_ROOT_PASSWORD
```

---

### **3️⃣ S3 접근 오류**

```
botocore.exceptions.NoCredentialsError: Unable to locate credentials
```

**해결:**
```bash
# .env 파일 확인
cat .env | grep AWS

# 환경 변수 로드 확인
docker-compose exec api-server printenv | grep AWS
```

---

### **4️⃣ 모델 로드 실패**

```
ClientError: An error occurred (NoSuchKey) when calling the GetObject operation
```

**해결:**
```bash
# S3 경로 확인
aws s3 ls s3://your-bucket/models/weather-predictor-018/model_artifact/

# 예상 구조:
# models/weather-predictor-018/
#   ├── model_artifact/
#   │   ├── model.pkl
#   │   └── scaler.pkl
#   └── config/
#       ├── train_config.json
#       └── feature_columns.json
```

---

### **5️⃣ 캐시가 작동하지 않음**

```python
# 로그 확인
docker-compose logs api-server | grep "캐시"

# 예상 출력:
# ✅ 캐시 HIT: 2025-10-01 14:00:00
# 🔄 캐시 MISS: 2025-10-01 15:00:00 최초 예측
```

**MySQL 데이터 확인:**
```sql
-- phpMyAdmin (http://localhost:8080) 접속 후
SELECT * FROM weather_predictions 
ORDER BY prediction_datetime DESC 
LIMIT 10;
```

---

### **6️⃣ 프론트엔드 빌드 오류**

```
Error: Cannot find module 'chart.js'
```

**해결:**
```bash
# frontend 디렉토리에서
cd frontend
npm install chart.js
npm run build
```

---

## 📊 성능 최적화

### **캐싱 효과**

| 항목 | 캐시 MISS | 캐시 HIT | 개선율 |
|------|-----------|----------|--------|
| 응답 시간 | 3-5초 | 50-100ms | **98%** |
| S3 API 호출 | 5회 | 0회 | **100%** |
| ML 연산 | 1회 | 0회 | **100%** |
| 비용 | $0.001 | $0 | **100%** |

### **예상 시나리오 (하루 1,000명 사용자)**

- **캐시 없을 때**: 1,000회 ML 예측 = 3,000-5,000초 = **50-83분**
- **캐시 있을 때**: 24회 ML 예측 (시간당 1회) = 72-120초 = **1-2분**

**시간 절약:** 약 **98%** ⚡

---

## 📈 향후 개선 사항

1. **로그 로테이션 설정**
   - healthcheck 로그 필터링
   - 로그 크기 제한 (max-size: 10MB)

2. **API 캐싱 확장**
   - Redis 도입 (인메모리 캐싱)
   - 다중 지역 지원 (station_id 확장)

3. **모니터링 추가**
   - Prometheus + Grafana
   - 예측 정확도 추적
   - 응답 시간 메트릭

4. **CI/CD 파이프라인**
   - GitHub Actions
   - 자동 테스트 및 배포

5. **보안 강화**
   - API Key 인증
   - Rate Limiting
   - HTTPS 적용

---

## 📝 참고 문서

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Next.js 공식 문서](https://nextjs.org/docs)
- [Chart.js 공식 문서](https://www.chartjs.org/)
- [MySQL 8.0 문서](https://dev.mysql.com/doc/refman/8.0/en/)
- [Boto3 S3 문서](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)

---

## 👥 기여자

- **Backend (FastAPI)**: api/main.py
- **Frontend (Next.js)**: frontend/pages/index.js
- **ML Pipeline**: src/models/batch_predict.py
- **Database**: src/storage/mysql_client.py

---

## 📄 라이센스

MIT License

---

**🌤️ 출퇴근길 날씨 친구 - MLOps 프로젝트**  
*실시간 쾌적지수 예측으로 더 나은 하루를 시작하세요!* 