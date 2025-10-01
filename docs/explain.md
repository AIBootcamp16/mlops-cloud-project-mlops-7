
# 프론트와 백엔드 도커 파일 분리하는 이유유

두 Dockerfile을 보니 프론트엔드(Next.js)와 백엔드(Python ML) 애플리케이션을 위한 것이네요. 분리하는 주요 이유들을 설명드리겠습니다:

## 🎯 **Dockerfile 분리 이유**

### 1. **기술 스택이 완전히 다름**
- **프론트엔드**: Node.js 18 기반 (Next.js 프레임워크)
- **백엔드**: Python 3.11 기반 (ML/데이터 처리)
- 각각 다른 베이스 이미지가 필요합니다

### 2. **의존성 관리가 독립적**
```12:13:frontend/Dockerfile
# Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```
- 프론트엔드: `package.json` (npm 패키지)
- 백엔드: `requirements.txt` (pip 패키지)
- 서로 영향을 주지 않고 업데이트 가능

### 3. **빌드 프로세스가 다름**
- **프론트엔드**: 
  ```16:17:frontend/Dockerfile
  # Next.js 빌드 (프로덕션용)
  RUN npm run build
  ```
  - 정적 자산 번들링, 최적화
  
- **백엔드**: 
  - ML 모델 로딩, 데이터 처리
  - gcc, g++ 같은 컴파일러 필요

### 4. **독립적인 배포 및 스케일링**
- 프론트엔드와 백엔드의 트래픽 패턴이 다를 수 있음
- 각각 독립적으로 스케일 업/다운 가능
- 한쪽만 업데이트해도 다른 쪽에 영향 없음

### 5. **이미지 크기 최적화**
- 프론트엔드: `node:18-alpine` (경량)
- 백엔드: ML 라이브러리 포함 (더 무거움)
- 필요한 것만 포함하여 이미지 크기 절감

### 6. **보안 및 격리**
- 각 컨테이너가 최소 권한 원칙 적용
- 프론트엔드 취약점이 백엔드에 영향 없음
- 네트워크 레벨에서 분리 가능

### 7. **마이크로서비스 아키텍처**
- 각 서비스가 독립적으로 개발/테스트/배포
- 팀 간 협업이 용이 (프론트 팀 vs 백엔드 팀)
- CI/CD 파이프라인도 분리 가능

이런 구조는 현대적인 웹 애플리케이션의 표준 패턴입니다. 당신의 프로젝트는 `docker-compose.yml`에서 이 두 서비스를 오케스트레이션하고 있을 것입니다! 👍

# fastAPI & index.js

`main.py`와 `index.js` 파일을 분석하여 API 연동 구조를 정리해드리겠습니다.

## 📡 API 연동 구조 정리

### **1. API 기본 설정**

```12:12:frontend/pages/index.js
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
```
- 프론트엔드는 `NEXT_PUBLIC_API_URL` 환경변수 사용
- 기본값: `http://localhost:8000`

---

### **2. 백엔드 API 엔드포인트 (main.py)**

#### 📌 **엔드포인트 목록**

| 메서드 | 경로 | 설명 | 프론트 사용 여부 |
|--------|------|------|------------------|
| GET | `/` | API 정보 반환 | ❌ |
| GET | `/health` | 헬스체크 | ❌ |
| GET | `/predict/{prediction_type}` | 쾌적지수 예측 | ✅ |
| GET | `/api/welcome` | 시간대별 환영 메시지 | ✅ |

---

### **3. 프론트엔드에서 실제 사용하는 API**

#### ✅ **API #1: 환영 메시지 가져오기**

**호출 위치:**
```15:32:frontend/pages/index.js
useEffect(() => {
    const fetchWelcomeMessage = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/welcome`);
        const data = await response.json();
        if (response.ok) {
          setWelcomeMessage(data.message);
        } else {
          setWelcomeMessage("안녕하세요! 😊<br/>날씨 예측 서비스입니다!");
        }
      } catch (error) {
        console.log("환영 메시지 로드 실패:", error);
        setWelcomeMessage("안녕하세요! 😊<br/>날씨 예측 서비스입니다!");
      }
    };

    fetchWelcomeMessage();
  }, [API_BASE_URL]);
```

**백엔드 구현:**
```137:161:api/main.py
@app.get("/api/welcome")
def get_welcome_message():
    """시간대별 환영 메시지"""
    kst = pytz.timezone('Asia/Seoul')
    current_time = datetime.now(kst)
    hour = current_time.hour
    
    if 5 <= hour < 9:
        message = "좋은 아침이에요! 😊<br>오늘 하루도 화이팅입니다! ☀️"
    elif 9 <= hour < 12:
        message = "활기찬 오전이네요! 💪<br>오늘도 좋은 하루 되세요! ✨"
    elif 12 <= hour < 14:
        message = "점심시간이에요! 🍽️<br>맛있는 식사 하시고 힘내세요! 😋"
    elif 14 <= hour < 18:
        message = "근무하시느라 힘드시죠? 💼<br>조금만 더 힘내세요! 응원합니다! 📈"
    elif 18 <= hour < 22:
        message = "오늘도 고생 많으셨어요! 😊<br>푹 쉬시고 좋은 저녁 되세요! 🌆"
    else:
        message = "늦은 시간이네요! 🌙<br>푹 쉬시고 내일도 좋은 하루 되세요! 💤"
    
    return {
        "message": message,
        "current_time": current_time.strftime("%Y-%m-%d %H:%M"),
        "hour": hour
    }
```

**응답 형식:**
```json
{
  "message": "좋은 아침이에요! 😊<br>오늘 하루도 화이팅입니다! ☀️",
  "current_time": "2025-10-01 08:30",
  "hour": 8
}
```

---

#### ✅ **API #2: 쾌적지수 예측**

**호출 위치:**
```105:127:frontend/pages/index.js
const getPrediction = async (type) => {
    setLoading(true);
    setResult(null);
    setShowResult(false);

    try {
      const response = await fetch(`${API_BASE_URL}/predict/${type}`);
      const data = await response.json();

      if (response.ok) {
        setResult(data);
        setTimeout(() => setShowResult(true), 100);
      } else {
        setResult({ error: `API 오류: ${response.status}`, details: data.detail });
        setTimeout(() => setShowResult(true), 100);
      }
    } catch (error) {
      setResult({ error: `네트워크 오류: ${error.message}` });
      setTimeout(() => setShowResult(true), 100);
    } finally {
      setLoading(false);
    }
  };
```

**버튼 클릭 시 호출:**
```259:271:frontend/pages/index.js
<button className="btn-primary" onClick={() => getPrediction('now')}>
            <span className="btn-icon">📱</span>
            <span className="btn-text">지금 날씨</span>
          </button>
          <button className="btn-primary" onClick={() => getPrediction('morning')}>
            <span className="btn-icon">🌅</span>
            <span className="btn-text">출근길 예측</span>
          </button>
          <button className="btn-primary" onClick={() => getPrediction('evening')}>
            <span className="btn-icon">🌆</span>
            <span className="btn-text">퇴근길 예측</span>
          </button>
```

**백엔드 구현:**
```51:135:api/main.py
@app.get("/predict/{prediction_type}")
def get_comfort_score(prediction_type: str):
    """쾌적지수 예측 (캐시 우선 조회)"""
    if prediction_type not in ["now", "morning", "evening"]:
        raise HTTPException(status_code=400, detail="prediction_type은 now, morning, evening 중 하나여야 합니다")
    
    try:
        # 1. 현재 시간대 (정각 기준) - KST
        kst = pytz.timezone('Asia/Seoul')
        current_hour = datetime.now(kst).replace(minute=0, second=0, microsecond=0)
        
        # 2. MySQL에서 캐시 조회
        cached = query_prediction_by_datetime(current_hour)
        
        if cached:
            # ✅ 캐시 HIT
            print(f"✅ 캐시 HIT: {current_hour}")
            comfort_score = cached['comfort_score']
            weather_data = {
                'temperature': cached.get('temperature'),
                'humidity': cached.get('humidity'),
                'rainfall': cached.get('rainfall'),
                'pm10': cached.get('pm10'),
                'wind_speed': cached.get('wind_speed'),
                'pressure': cached.get('pressure'),
                'region': cached.get('region'),
                'station_id': cached.get('station_id')
            }
        else:
            # ❌ 캐시 MISS: 최초 예측
            print(f"🔄 캐시 MISS: {current_hour} 최초 예측")
            result_df = batch_predict(experiment_name='weather-predictor-018')
            
            # station_id 108번만 필터링
            station_108 = result_df[result_df['station_id'] == '108'].iloc[0]
            
            # MySQL에 저장 (전체 지역)
            save_prediction_to_mysql(result_df, current_hour)
            
            # 결과 추출 (station_id 108만)
            comfort_score = station_108['predicted_comfort_score']
            weather_data = {
                'temperature': station_108.get('temperature'),
                'humidity': station_108.get('humidity'),
                'rainfall': station_108.get('rainfall'),
                'pm10': station_108.get('pm10'),
                'wind_speed': station_108.get('wind_speed'),
                'pressure': station_108.get('pressure'),
                'region': station_108.get('region'),
                'station_id': station_108.get('station_id')
            }
        
        # 3. 응답 생성
        titles = {
            "now": "📱 현재 시점 예측",
            "morning": "🌅 출근길 예측 (6-9시)", 
            "evening": "🌆 퇴근길 예측 (18-21시)"
        }
        
        if comfort_score >= 80:
            label = "excellent"
            evaluation = "완벽한 날씨입니다! 🌟"
        elif comfort_score >= 60:
            label = "good" 
            evaluation = "쾌적한 날씨입니다! 😊"
        elif comfort_score >= 40:
            label = "fair"
            evaluation = "보통 날씨입니다 😐"
        else:
            label = "poor"
            evaluation = "날씨가 좋지 않습니다 ⚠️"
        
        return {
            "title": titles[prediction_type],
            "score": round(comfort_score, 1),
            "label": label,
            "evaluation": evaluation,
            "prediction_time": current_hour.strftime("%Y-%m-%d %H:%M"),
            "weather_data": weather_data,
            "prediction_type": prediction_type,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"예측 중 오류 발생: {str(e)}")
```

**응답 형식:**
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

---

### **4. CORS 설정**

```27:34:api/main.py
# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
- 프론트엔드 포트 3000, 3001에서의 요청 허용

---

### **5. API 호출 흐름 요약**

```
┌─────────────────────┐
│  프론트엔드 로딩     │
│  (index.js)         │
└──────────┬──────────┘
           │
           ├─── 1️⃣ GET /api/welcome
           │    └─> 시간대별 환영 메시지 표시
           │
           ├─── 2️⃣ 사용자 버튼 클릭
           │    │
           │    ├─ "지금 날씨" → GET /predict/now
           │    ├─ "출근길" → GET /predict/morning  
           │    └─ "퇴근길" → GET /predict/evening
           │         │
           │         └─> MySQL 캐시 확인
           │              ├─ HIT: 저장된 데이터 반환
           │              └─ MISS: ML 모델 예측 → MySQL 저장 → 반환
           │
           └─── 3️⃣ 결과 화면 렌더링
                 ├─ 쾌적지수 원형 게이지
                 ├─ 날씨 정보 (온도, 습도, 미세먼지 등)
                 └─ 예측 시간
```

---

### **6. 사용되지 않는 API**

- `GET /` - 루트 엔드포인트 (API 정보만 제공)
- `GET /health` - 헬스체크 (모니터링용)

이 두 API는 개발/모니터링 목적으로 존재하지만 프론트엔드에서는 직접 호출하지 않습니다.

네, 로그에 남습니다! 하지만 **레벨에 따라 다르게 기록**됩니다.

## 📝 로그 기록 방식

### **1. Uvicorn Access Log (서버 레벨)** ✅

모든 HTTP 요청이 자동으로 기록됩니다:

```bash
INFO:     127.0.0.1:52341 - "GET / HTTP/1.1" 200 OK
INFO:     127.0.0.1:52342 - "GET /health HTTP/1.1" 200 OK
INFO:     127.0.0.1:52343 - "GET /predict/now HTTP/1.1" 200 OK
INFO:     127.0.0.1:52344 - "GET /api/welcome HTTP/1.1" 200 OK
```

### **2. Application Log (코드 내부)** ⚠️

현재 `main.py`를 보면 **`/predict` 엔드포인트만** 명시적으로 로그를 남기고 있습니다:

```67:68:api/main.py
            print(f"✅ 캐시 HIT: {current_hour}")
```

```81:81:api/main.py
            print(f"🔄 캐시 MISS: {current_hour} 최초 예측")
```

**`/`와 `/health`는 코드 내부 로그가 없습니다.**

---

## 🚨 헬스체크 로그 문제

`/health` 엔드포인트는 특히 주의가 필요합니다:

### **왜 문제가 될까?**

1. **로드밸런서/쿠버네티스**가 30초마다 자동 호출
2. **모니터링 도구**가 1분마다 확인
3. **Docker Compose healthcheck** 설정 시 주기적 호출

```bash
# 예시: 30초마다 호출되면...
INFO:     127.0.0.1:52341 - "GET /health HTTP/1.1" 200 OK
INFO:     127.0.0.1:52342 - "GET /health HTTP/1.1" 200 OK
INFO:     127.0.0.1:52343 - "GET /health HTTP/1.1" 200 OK
INFO:     127.0.0.1:52344 - "GET /health HTTP/1.1" 200 OK
... (무한 반복) ...
```

**→ 로그 파일이 빠르게 커져서 디스크를 가득 채울 수 있습니다!**

---

## 💡 해결 방법
Read file: /home/realtheai/mlops-cloud-project-mlops-7/api/main.py

### **방법 1: 헬스체크 로그 제외 (추천)**

```python
# main.py 수정
import logging
from fastapi.logger import logger as fastapi_logger

# 헬스체크 로그 필터 추가
class HealthCheckFilter(logging.Filter):
    def filter(self, record):
        return "/health" not in record.getMessage()

# 로거 설정
logging.getLogger("uvicorn.access").addFilter(HealthCheckFilter())
```

### **방법 2: Uvicorn 실행 시 설정**

```python
# main.py 마지막 부분
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info",  # debug, info, warning, error
        access_log=True    # False로 설정하면 access log 비활성화
    )
```

### **방법 3: 로그 로테이션 설정**

```yaml
# docker-compose.yml에 추가
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"      # 로그 파일 최대 크기
        max-file: "3"         # 보관할 로그 파일 개수
```

---

## 📊 로그 확인 방법

```bash
# Docker 컨테이너 로그 보기
docker logs mlops-backend

# 실시간 로그 스트리밍
docker logs -f mlops-backend

# 최근 100줄만 보기
docker logs --tail 100 mlops-backend

# /health 제외하고 보기
docker logs mlops-backend | grep -v "/health"
```

---

## ✅ 요약

| 엔드포인트 | Uvicorn Log | Application Log | 주의사항 |
|-----------|-------------|-----------------|---------|
| `GET /` | ✅ | ❌ | 일반적으로 적게 호출됨 |
| `GET /health` | ✅ | ❌ | **⚠️ 자주 호출되어 로그 과다** |
| `GET /predict/*` | ✅ | ✅ (print 포함) | 중요한 비즈니스 로직 |
| `GET /api/welcome` | ✅ | ❌ | 페이지 로드 시마다 호출 |

**결론:** 모든 요청은 기본적으로 로그에 남지만, `/health`는 로그 필터링이나 로테이션 설정을 해주는 것이 좋습니다! 🎯

지금 코드 그대로 실행하면 이렇게 됩니다:

## 🔄 **현재 상태 (별도 설정 없음)**

### **1. 모든 요청이 로그에 기록됨** ✅

```bash
# 터미널/Docker 로그에 이렇게 출력됩니다
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000

# 요청마다...
INFO:     172.18.0.1:50234 - "GET / HTTP/1.1" 200 OK
INFO:     172.18.0.1:50235 - "GET /health HTTP/1.1" 200 OK
INFO:     172.18.0.1:50236 - "GET /api/welcome HTTP/1.1" 200 OK
✅ 캐시 HIT: 2025-10-01 14:00:00
INFO:     172.18.0.1:50237 - "GET /predict/now HTTP/1.1" 200 OK
```

---

### **2. 헬스체크 모니터링이 없다면** 😌

만약 **로드밸런서, 쿠버네티스, Docker healthcheck**를 설정하지 않았다면:
- `/health`는 수동 호출할 때만 로그에 남음
- **문제 없음**, 로그가 깔끔하게 유지됨

```bash
# 하루에 이 정도만 기록됨 (가볍게)
INFO:     172.18.0.1:50236 - "GET /api/welcome HTTP/1.1" 200 OK
✅ 캐시 HIT: 2025-10-01 09:00:00
INFO:     172.18.0.1:50237 - "GET /predict/now HTTP/1.1" 200 OK
🔄 캐시 MISS: 2025-10-01 10:00:00 최초 예측
INFO:     172.18.0.1:50238 - "GET /predict/morning HTTP/1.1" 200 OK
```

---

### **3. Docker Compose healthcheck가 있다면** ⚠️
Read file: /home/realtheai/mlops-cloud-project-mlops-7/docker-compose.yml

좋은 소식입니다! **`docker-compose.yml`에 healthcheck 설정이 없네요** ✅

## 📝 **현재 상태로 실행 시**

### ✅ **정상 작동 (문제 없음)**

```bash
# 실제 로그 예시 (하루 기준)
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000

# 사용자가 프론트엔드 접속할 때
INFO:     172.18.0.1:50236 - "GET /api/welcome HTTP/1.1" 200 OK

# 사용자가 "지금 날씨" 버튼 클릭
✅ 캐시 HIT: 2025-10-01 14:00:00
INFO:     172.18.0.1:50237 - "GET /predict/now HTTP/1.1" 200 OK

# 사용자가 "출근길" 버튼 클릭  
🔄 캐시 MISS: 2025-10-01 09:00:00 최초 예측
INFO:     172.18.0.1:50238 - "GET /predict/morning HTTP/1.1" 200 OK

# /health는 수동 호출할 때만 (거의 없음)
INFO:     172.18.0.1:50239 - "GET /health HTTP/1.1" 200 OK
```

---

### 📊 **예상 로그 양**

| 상황 | 하루 로그 예상량 |
|-----|----------------|
| **개발/테스트** | 100~500줄 (적음) |
| **실 사용자 10명** | 1,000~2,000줄 (보통) |
| **실 사용자 100명** | 10,000~20,000줄 (많음, 하지만 관리 가능) |

**→ 현재는 전혀 문제없습니다!** 😊

---

### ⚠️ **주의해야 할 시점**

나중에 이런 설정을 추가하면 로그가 폭증합니다:

```yaml
# ❌ 이런 설정 추가하면 로그 폭증!
services:
  api-server:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s      # 30초마다 호출
      timeout: 10s
      retries: 3
```

**계산:**
- 30초마다 1번 = 하루 2,880번 호출
- 로그 1줄 = 약 100바이트
- **하루 약 280KB** (healthcheck만)
- 한 달이면 **8.4MB**
- 1년이면 **100MB+**

---

### ✅ **결론**

**지금 그대로 사용하면:**

1. **로그는 정상적으로 기록됨** ✅
2. **로그 양은 적당함** (사용자 활동에 비례)
3. **디스크 용량 문제 없음** ✅
4. **별도 조치 불필요** ✅

**단, 나중에 프로덕션 배포 시:**
- 쿠버네티스, AWS ECS, 로드밸런서 도입
- Healthcheck 추가 시
- 로그 로테이션/필터링 설정 고려 필요

**현재는 그대로 사용하셔도 됩니다!** 🎯

