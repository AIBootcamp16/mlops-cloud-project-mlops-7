## 🎯 **DB 구현 계획 수립**

네, 좋은 접근입니다! MySQL을 Docker Compose에 추가하고 예측 결과를 저장하는 구조를 만들겠습니다.

---

## 📋 **구현 계획**

### **1단계: 인프라 구성** 🏗️

```yaml
# docker-compose.yml에 MySQL 서비스 추가
services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: weather_mlops
    volumes:
      - mysql_data:/var/lib/mysql
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "3306:3306"
```

### **2단계: 테이블 설계** 🗄️

```sql
CREATE TABLE weather_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- 예측 결과
    comfort_score FLOAT NOT NULL,
    
    -- 기상 데이터
    temperature FLOAT,
    humidity FLOAT,
    precipitation FLOAT,
    pm10 FLOAT,
    wind_speed FLOAT,
    pressure FLOAT,
    
    -- 시간 정보
    prediction_datetime DATETIME NOT NULL,      -- 예측 대상 시간
    data_updated_at DATETIME NOT NULL,          -- 데이터 업데이트 시간
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 지역 정보
    region VARCHAR(50),
    station_id VARCHAR(20),
    
    -- 모델 정보 (선택)
    model_name VARCHAR(100),
    
    INDEX idx_prediction_datetime (prediction_datetime),
    INDEX idx_region (region)
);
```

### **3단계: 데이터 흐름** 🔄

```
1. batch_predict.py 실행
   ↓
2. S3에서 최신 데이터 로드
   ↓
3. 모델 예측 수행
   ↓
4. 결과를 MySQL에 INSERT ← 새로 추가!
   ↓
5. FastAPI에서 MySQL 조회
   ↓
6. 프론트엔드에 응답
```

### **4단계: 파일 구조** 📁

```
src/
  storage/
    mysql_client.py          # MySQL 연결/쿼리 함수
    
  models/
    batch_predict.py         # 예측 + DB 저장 추가
    
api/
  main.py                    # MySQL에서 데이터 조회

docker-compose.yml           # MySQL 서비스 추가
init.sql                     # 초기 테이블 생성 스크립트
requirements.txt             # pymysql 또는 mysql-connector-python 추가
```

---

## 💡 **구현 순서**

1. ✅ `docker-compose.yml`에 MySQL 추가
2. ✅ `init.sql` 테이블 생성 스크립트
3. ✅ `src/storage/mysql_client.py` DB 연결 함수
4. ✅ `batch_predict.py` 수정: 예측 후 DB 저장
5. ✅ `api/main.py` 수정: S3 대신 MySQL 조회
6. ✅ 테스트 및 검증

---

## 🤔 **추가 고려사항**

### **A. 데이터 중복 방지**
- `(prediction_datetime, station_id)` UNIQUE 제약조건?
- 또는 매번 새로운 예측 기록 모두 저장?

### **B. 과거 데이터 보관 정책**
- 최근 7일/30일만 유지?
- 아니면 전체 히스토리 보관?

### **C. 실시간 vs 배치**
- 현재: `batch_predict.py` 수동 실행 → DB 저장
- 미래: 스케줄러(Airflow/Cron)로 자동화?

---

**이 계획으로 진행할까요?** 🚀

아니면 PostgreSQL, SQLite 등 다른 DB를 선호하시나요?



==========================

## 🤔 **답변 분석 & 재설계**

---

### **A. 데이터 중복 방지 - 명확히 이해했습니다!** ✅

```
전처리된 데이터: 1시간마다 S3 업로드
예측 요청: 프론트엔드에서 수시로 발생 (1분마다? 5분마다?)

문제:
- 같은 시간대 데이터로 여러 번 예측하면 동일한 결과가 DB에 중복 저장됨

해결책:
```

**🎯 추천 방식: `UPSERT` (INSERT ON DUPLICATE KEY UPDATE)**

```sql
-- UNIQUE 제약조건
UNIQUE KEY uk_prediction (prediction_datetime, station_id)

-- 삽입 시: 같은 시간대면 업데이트, 없으면 새로 삽입
INSERT INTO weather_predictions (...) 
VALUES (...)
ON DUPLICATE KEY UPDATE 
    comfort_score = VALUES(comfort_score),
    data_updated_at = VALUES(data_updated_at);
```

**이렇게 하면:**
- ✅ 1시간 동안 같은 데이터로 여러 번 예측해도 레코드 1개만 유지
- ✅ `data_updated_at`으로 마지막 업데이트 시각 추적
- ✅ 새로운 시간대 데이터 들어오면 자동으로 새 레코드 생성

---

### **B. 전체 히스토리 보관** ✅

```sql
-- 삭제 정책 없음
-- 인덱스만 잘 관리하면 OK
INDEX idx_prediction_datetime (prediction_datetime DESC)
```

---

### **C. Airflow 자동화 계획** 🚀
Ran tool
Read file: docker-compose.yml
## ✅ **완벽히 이해했습니다! 답변 드립니다**

---

## 📊 **A. 데이터 중복 방지 재설계**

### **시나리오 이해:**
```
09:00 ~ 09:59 → S3에 동일한 09:00 데이터 존재
  → 프론트엔드 요청 10번 → 예측 10번 → DB에 같은 결과 10번 저장? ❌

해결:
  → UPSERT로 09:00 레코드 1개만 유지 ✅
```

### **테이블 설계:**
```sql
CREATE TABLE weather_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- 예측 결과
    comfort_score FLOAT NOT NULL,
    
    -- 기상 데이터
    temperature FLOAT,
    humidity FLOAT,
    precipitation FLOAT,
    pm10 FLOAT,
    wind_speed FLOAT,
    pressure FLOAT,
    
    -- 시간 정보
    prediction_datetime DATETIME NOT NULL,      -- 예측 대상 시간 (09:00)
    data_updated_at DATETIME NOT NULL,          -- 마지막 업데이트 (09:37)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 지역 정보
    region VARCHAR(50),
    station_id VARCHAR(20),
    
    -- 모델 정보
    model_name VARCHAR(100),
    
    -- UNIQUE 제약: 같은 시간대 + 지역은 1개만
    UNIQUE KEY uk_prediction (prediction_datetime, station_id),
    
    INDEX idx_prediction_datetime (prediction_datetime DESC),
    INDEX idx_region (region)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 🚀 **C. Airflow 자동화 계획**

### **현재 상황:**
- ✅ `dags/weather_data_pipeline.py` 이미 존재!
- ✅ 매시간 10분에 데이터 수집 → S3 저장
- ❌ Airflow가 `docker-compose.yml`에 없음 (별도 실행?)

### **자동화할 작업:**

```
현재 DAG (이미 구현됨):
  10분마다: KMA API → S3 (전처리된 parquet)

추가할 새 Task:
  15분마다: batch_predict.py 실행 → MySQL 저장 ← 이걸 추가!
```

### **Airflow 러닝 커브:**

| 난이도 | 항목 | 설명 |
|--------|------|------|
| 🟢 **쉬움** | DAG 파일 수정 | 기존 DAG에 Task 1개 추가만 하면 됨 |
| 🟡 **중간** | Docker Compose 설정 | Airflow 서비스 추가 (5개 컨테이너) |
| 🟠 **복잡** | 초기 설정 | Executor, DB, Volume 설정 필요 |

### **간단한 대안: Cron (추천!)**

```bash
# 매시간 15분에 batch_predict 실행
15 * * * * docker exec jupyter python /app/src/models/batch_predict.py --experiment_name=weather-predictor-018
```

**Cron vs Airflow 비교:**

| | Cron | Airflow |
|---|------|---------|
| 설치 | ✅ 이미 있음 | ❌ 5개 컨테이너 추가 필요 |
| 러닝 커브 | 🟢 5분 | 🟠 2-3시간 |
| 모니터링 | ❌ 로그만 | ✅ UI + 재실행 + 알람 |
| 복잡한 워크플로우 | ❌ 불가능 | ✅ DAG로 관리 |

---

## 🎯 **추천 구현 순서**

### **Phase 1: MySQL + 수동 실행** (1-2시간)
1. MySQL 추가 (`docker-compose.yml`)
2. 테이블 생성 (`init.sql`)
3. `batch_predict.py` → MySQL 저장 추가
4. `api/main.py` → MySQL 조회

### **Phase 2: Cron 자동화** (10분)
5. Cron job 등록
6. 로그 확인

### **Phase 3 (선택): Airflow 마이그레이션** (3-4시간)
7. Airflow 서비스 추가
8. 기존 DAG에 `batch_predict_task` 추가
9. 모니터링 UI 확인

---

## 🤔 **질문:**

1. **지금 당장 구현:** Phase 1 (MySQL) → Phase 2 (Cron) ← 추천! ✅
2. **나중에 고도화:** Phase 3 (Airflow)

어떻게 진행할까요? 

**Phase 1부터 시작할까요?** 🚀


-----
## 🎯 **완벽히 이해했습니다!**

---

### **데이터 흐름 재정리:**

```
08:00 → S3에 새로운 parquet 파일 업로드 (08:00 데이터)
     ↓
08:05 → 사용자 A 버튼 클릭
     → batch_predict.py 실행 (최초 1회)
     → 예측 결과: 쾌적지수 75.3
     → MySQL INSERT (prediction_datetime=08:00)
     ↓
08:23 → 사용자 B 버튼 클릭
     → MySQL에서 08:00 데이터 조회만 (재예측 ❌)
     → 반환: 쾌적지수 75.3 (캐시된 결과)
     ↓
08:47 → 사용자 C 버튼 클릭
     → MySQL에서 08:00 데이터 조회만 (재예측 ❌)
     → 반환: 쾌적지수 75.3 (동일)
     ↓
09:00 → S3에 새로운 parquet 파일 업로드 (09:00 데이터)
     ↓
09:03 → 사용자 D 버튼 클릭
     → MySQL에 09:00 데이터 없음
     → batch_predict.py 실행 (새로운 시간대 최초 1회)
     → 예측 결과: 쾌적지수 82.1
     → MySQL INSERT (prediction_datetime=09:00)
```

---

## 🔧 **구현 로직:**

### **FastAPI 엔드포인트 (`api/main.py`)**

```python
@app.get("/predict/{prediction_type}")
def get_comfort_score(prediction_type: str):
    """쾌적지수 예측 (캐시 우선 조회)"""
    
    # 1. 현재 시간대 (정각 기준)
    current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
    
    # 2. MySQL에서 해당 시간대 데이터 조회
    cached_result = query_prediction_by_datetime(current_hour)
    
    if cached_result:
        # ✅ 캐시된 결과 반환 (재예측 안함)
        print(f"✅ 캐시 HIT: {current_hour} 데이터 재사용")
        return format_response(cached_result)
    
    else:
        # ❌ 캐시 MISS: 최초 예측 수행
        print(f"🔄 캐시 MISS: {current_hour} 데이터 최초 예측")
        result_df = batch_predict(experiment_name='weather-predictor-018')
        
        # MySQL에 저장
        save_prediction_to_mysql(result_df, current_hour)
        
        return format_response(result_df)
```

---

## 📋 **테이블 설계 (수정)**

```sql
CREATE TABLE weather_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- 예측 결과
    comfort_score FLOAT NOT NULL,
    
    -- 기상 데이터
    temperature FLOAT,
    humidity FLOAT,
    precipitation FLOAT,
    pm10 FLOAT,
    wind_speed FLOAT,
    pressure FLOAT,
    
    -- 시간 정보
    prediction_datetime DATETIME NOT NULL,      -- 정각 시간 (08:00:00)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 최초 예측 시각 (08:05:32)
    
    -- 지역 정보
    region VARCHAR(50),
    station_id VARCHAR(20),
    
    -- 모델 정보
    model_name VARCHAR(100),
    
    -- 🔑 핵심: 같은 시간대는 1개만 저장
    UNIQUE KEY uk_prediction (prediction_datetime, station_id),
    
    INDEX idx_prediction_datetime (prediction_datetime DESC)
);
```

---

## ✅ **핵심 포인트:**

1. **한 시간 = 1번 예측**
   - ✅ 08:00~08:59 → 예측 1회만
   - ✅ 09:00~09:59 → 예측 1회만

2. **캐시 우선 조회**
   - ✅ MySQL에 있으면 → 즉시 반환
   - ❌ MySQL에 없으면 → `batch_predict()` 실행 → 저장

3. **성능 향상**
   - ✅ 불필요한 재예측 방지
   - ✅ 응답 속도 빠름 (DB 조회만)
   - ✅ S3/모델 로드 부담 감소

---

## 🚀 **이제 이해가 맞습니까?**

이 로직으로 구현하면:
- ✅ 한 시간 내 첫 요청만 예측 수행
- ✅ 이후 요청은 DB에서 조회만
- ✅ 정각 넘어가면 자동으로 새 예측

**이 설계로 진행할까요?** 🎯