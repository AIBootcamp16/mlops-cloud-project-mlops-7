# FastAPI 서버 사용법

## 🚀 서버 실행

**방법 1: 직접 실행**
```bash
cd src/serving
python server.py
```

**방법 2: uvicorn 사용 (추천)**
```bash
cd src/serving
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

**uvicorn 장점:**
- `--reload`: 파일 변경 시 자동 재시작
- `--host 0.0.0.0`: 외부 접속 허용
- 더 많은 옵션 제어 가능
- 프로덕션 환경에 적합

**서버 정보:**
- URL: http://localhost:8000
- API 문서: http://localhost:8000/docs
- 타이틀: "출퇴근길 쾌적지수 예측모델"

## 📡 API 엔드포인트

### 1. 기본 정보
```bash
GET /          # 서비스 상태
GET /health    # 헬스 체크
GET /stations  # 관측소 목록
```

### 2. 예측 API
```bash
POST /predict
```

**요청 예시:**
```json
{
  "station_ids": ["108", "112"],
  "datetime": "2025-09-25T14:00:00Z",
  "features": {
    "temperature": 23.5,
    "pm10": 15.0
  }
}
```

**응답 예시:**
```json
{
  "predictions": [
    {
      "station_id": "108",
      "datetime": "2025-09-25T14:00:00Z",
      "predicted_temperature": 24.1,
      "predicted_pm10": 16.3,
      "comfort_score": 78.2,
      "confidence": 0.89
    }
  ],
  "processing_time": 0.15
}
```

## 🔄 실제 모델 전환

**현재 (Mock 모델):**
```python
# Mock 예측 로직 사용 중
predictions = []  # 랜덤 값 생성
```

**모델링팀 완성 후:**
```python
# 1. joblib import 주석 해제
import joblib

# 2. Mock 예측 부분을 실제 모델로 교체
model = joblib.load("models/weather_model.pkl")
predictions = model.predict(ml_features).to_dict('records')
```

## 🧪 테스트

```bash
cd tests
python test_api.py
```

---

**작성일**: 2025-09-25
**파일**: `src/serving/server.py`