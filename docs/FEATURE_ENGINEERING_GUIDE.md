# 피처 엔지니어링 가이드

**작성일**: 2025-01-27
**파일**: `src/features/feature_builder.py`
**목적**: 원시 기상 데이터를 ML 학습용 피처로 변환하는 과정 상세 설명

## 📊 데이터 변환 흐름

```
원시 CSV (48개 컬럼) → 기본 피처 추출 (13개) → 피처 엔지니어링 (34개 총)
```

## 🔄 1단계: 원시 데이터 → 기본 피처

### 원시 데이터 (`weather_pm10_integrated_full.csv`)
```
YYMMDDHHMI,STN,WD,WS,GST,GST_2,GST_3,PA,PS,PT,PR,TA,TD,HM,PV,RN,RN_2,RN_3,RN_4,SD,SD_2,SD_3,WC,WP,WW,CA,CA_2,CH,CT,CT_2,CT_3,CT_4,VS,SS,SI,ST,TS,TE,TE_2,TE_3,TE_4,ST_2,WH,BF,IR,IX,datetime,PM10,PM10_FLAG
```

### 추출된 기본 피처 (13개)
| 원시 컬럼 | ML 피처 | 설명 | 변환 로직 |
|----------|---------|------|----------|
| `STN` | `station_id` | 관측소 ID | 문자열 변환 |
| `datetime` | `datetime` | 관측 시간 | datetime 변환 |
| `TA` | `temperature` | 기온 (°C) | 숫자 변환 |
| `PM10` | `pm10` | 미세먼지 농도 (μg/m³) | 숫자 변환 |
| `WS` | `wind_speed` | 풍속 (m/s) | 숫자 변환 |
| `HM` | `humidity` | 상대습도 (%) | 숫자 변환 |
| `PS` | `pressure` | 현지기압 (hPa) | 숫자 변환 |
| `RN` | `rainfall` | 강수량 (mm) | 숫자 변환 |
| `WD` | `wind_direction` | 풍향 (16방위) | 숫자 변환 |
| `TD` | `dew_point` | 이슬점온도 (°C) | 숫자 변환 |
| `CA` | `cloud_amount` | 운량 (10분위) | 숫자 변환 |
| `VS` | `visibility` | 시정 (m) | 숫자 변환 |
| `SS` | `sunshine` | 일조시간 (hr) | 숫자 변환 |

## 🛠️ 2단계: 피처 엔지니어링 (`add_engineered_features`)

### A. 시간 기반 피처 (8개)

| 피처명 | 데이터 타입 | 생성 로직 | 예시 |
|--------|-------------|----------|------|
| `hour` | int | `datetime.hour` | 9 |
| `day_of_week` | int | `datetime.dayofweek` (0=월, 6=일) | 0 |
| `month` | int | `datetime.month` | 1 |
| `is_rush_hour` | bool | `hour in [7,8,9,18,19,20]` | True |
| `is_morning_rush` | bool | `hour in [7,8,9]` | True |
| `is_evening_rush` | bool | `hour in [18,19,20]` | False |
| `is_weekday` | bool | `day_of_week < 5` | True |
| `is_weekend` | bool | `day_of_week >= 5` | False |
| `season` | str | 월 기준 계절 매핑 | 'winter' |

### B. 기온 기반 피처 (5개)

| 피처명 | 데이터 타입 | 생성 로직 | 예시 |
|--------|-------------|----------|------|
| `temp_category` | str | 온도 구간 분류 | 'very_cold' (-2.5°C) |
| `temp_comfort` | float | `20 - abs(temp - 20)` | -2.5 |
| `temp_extreme` | bool | `temp < 0 or temp > 30` | True |
| `heating_needed` | bool | `temp < 10` | True |
| `cooling_needed` | bool | `temp > 25` | False |

**온도 구간 분류:**
- `very_cold`: < 0°C
- `cold`: 0-10°C
- `mild`: 10-20°C
- `warm`: 20-30°C
- `hot`: > 30°C

### C. 지역 기반 피처 (3개)

| 피처명 | 데이터 타입 | 생성 로직 | 예시 |
|--------|-------------|----------|------|
| `is_metro_area` | bool | `station_id in 주요도시리스트` | True |
| `is_coastal` | bool | `station_id in 연안지역리스트` | False |
| `region` | str | 관측소 번호 첫자리 기준 권역 | 'central' |

**권역 분류:**
- `central`: 100번대 (중부권)
- `south`: 200번대 (남부권)
- `east`: 300번대 (동부권)
- `west`: 900번대 (서부권)

### D. 대기질 기반 피처 (3개)

| 피처명 | 데이터 타입 | 생성 로직 | 예시 |
|--------|-------------|----------|------|
| `pm10_grade` | str | 환경부 미세먼지 등급 기준 | 'good' |
| `mask_needed` | bool | `pm10 > 50` | False |
| `outdoor_activity_ok` | bool | `pm10 <= 80` | True |

**미세먼지 등급:**
- `good`: 0-30 μg/m³
- `moderate`: 31-80 μg/m³
- `unhealthy`: 81-150 μg/m³
- `very_unhealthy`: > 150 μg/m³

### E. 종합 쾌적지수 (1개)

| 피처명 | 데이터 타입 | 생성 로직 | 예시 |
|--------|-------------|----------|------|
| `comfort_score` | float | 기온(50%) + 미세먼지(30%) + 보정점수 | 18.0 |

**쾌적지수 계산 공식:**
```python
# 기본 점수 50점에서 시작
base_score = 50.0

# 기온 점수 (50% 비중)
if 15 <= temp <= 22: temp_score = 90  # 최적
elif 10 <= temp <= 25: temp_score = 70  # 적당
elif 5 <= temp <= 30: temp_score = 50   # 견딜만
elif 0 <= temp <= 35: temp_score = 20   # 불쾌
else: temp_score = 10  # 극한

# 미세먼지 점수 (30% 비중)
if pm10 <= 15: pm10_score = 90      # 매우 좋음
elif pm10 <= 35: pm10_score = 70    # 좋음
elif pm10 <= 75: pm10_score = 50    # 보통
elif pm10 <= 150: pm10_score = 30   # 나쁨
else: pm10_score = 10               # 매우 나쁨

# 최종 점수 계산
comfort_score = base_score * 0.5 + temp_score * 0.5
comfort_score = comfort_score * 0.7 + pm10_score * 0.3

# 보정 적용
comfort_score -= (is_rush_hour * 10)    # 출퇴근시간 -10점
comfort_score += (is_weekend * 5)       # 주말 +5점
comfort_score -= (temp_extreme * 20)    # 극한기온 -20점

# 0-100 범위로 제한
comfort_score = clip(comfort_score, 0, 100)
```

## 📋 최종 ML 데이터셋 스키마

**총 34개 피처:**

| 카테고리 | 피처 수 | 피처 리스트 |
|----------|---------|-------------|
| **기본 정보** | 2 | `station_id`, `datetime` |
| **원시 기상** | 11 | `temperature`, `pm10`, `wind_speed`, `humidity`, `pressure`, `rainfall`, `wind_direction`, `dew_point`, `cloud_amount`, `visibility`, `sunshine` |
| **시간 피처** | 8 | `hour`, `day_of_week`, `month`, `is_rush_hour`, `is_morning_rush`, `is_evening_rush`, `is_weekday`, `is_weekend`, `season` |
| **온도 피처** | 5 | `temp_category`, `temp_comfort`, `temp_extreme`, `heating_needed`, `cooling_needed` |
| **지역 피처** | 3 | `is_metro_area`, `is_coastal`, `region` |
| **대기질 피처** | 3 | `pm10_grade`, `mask_needed`, `outdoor_activity_ok` |
| **종합 지수** | 1 | `comfort_score` |

## 🎯 피처 엔지니어링 목적

1. **시간 패턴 포착**: 출퇴근시간, 계절성, 요일 패턴
2. **지역 특성 반영**: 도시/연안 지역 구분, 권역별 특성
3. **실용적 지표 생성**: 마스크 필요성, 야외활동 적합도
4. **종합 평가**: 다양한 기상 요소를 통합한 쾌적지수

## 💡 핵심 인사이트

- **기온**이 가장 중요한 요소 (쾌적지수 50% 비중)
- **미세먼지**가 두 번째 중요 요소 (30% 비중)
- **출퇴근시간**은 불편함을 가중시키는 요소 (-10점)
- **주말**은 쾌적함을 높이는 요소 (+5점)
- **극한 기온**은 쾌적도를 크게 떨어뜨림 (-20점)

## 🔍 실제 데이터 변환 예시

### 원시 데이터 1행:
```
202401010900,100,9,0.8,-9,-9.0,-9,936.9,1031.7,2,1.1,-2.5,-3.3,94.0,4.8,0.0,0.0,0.0,-9.0,-9.0,-9.0,18.7,-9,-9,-,8,8,5,-,-9,-9,-9,1328,0.0,0.01,-9,-1.5,-99.0,-99.0,-99.0,-99.0,-9,-9.0,-9,3,-9,2024-01-01 09:00:00,15.0,000000
```

### 변환된 ML 피처:
```python
{
    # 기본 정보
    'station_id': '100',
    'datetime': '2024-01-01 09:00:00',

    # 원시 기상 데이터
    'temperature': -2.5,        # TA 컬럼
    'pm10': 15.0,              # PM10 컬럼
    'wind_speed': 0.8,         # WS 컬럼
    'humidity': 94.0,          # HM 컬럼
    'pressure': 936.9,         # PS 컬럼
    'rainfall': 0.0,           # RN 컬럼
    'wind_direction': 9.0,     # WD 컬럼
    'dew_point': -3.3,         # TD 컬럼
    'cloud_amount': 8.0,       # CA 컬럼
    'visibility': 1328.0,      # VS 컬럼
    'sunshine': 0.0,           # SS 컬럼

    # 시간 피처
    'hour': 9,                 # 09시
    'day_of_week': 0,          # 월요일
    'month': 1,                # 1월
    'is_rush_hour': True,      # 9시는 출퇴근시간
    'is_morning_rush': True,   # 아침 출퇴근
    'is_evening_rush': False,  # 저녁 출퇴근 아님
    'is_weekday': True,        # 평일
    'is_weekend': False,       # 주말 아님
    'season': 'winter',        # 1월 = 겨울

    # 온도 피처
    'temp_category': 'very_cold',  # -2.5°C < 0
    'temp_comfort': -2.5,          # 20 - |-2.5 - 20| = -2.5
    'temp_extreme': True,          # -2.5 < 0
    'heating_needed': True,        # -2.5 < 10
    'cooling_needed': False,       # -2.5 < 25

    # 지역 피처
    'is_metro_area': True,     # 100번 = 서울 (주요도시)
    'is_coastal': False,       # 100번 ≠ 연안지역
    'region': 'central',       # 100번대 = 중부권

    # 대기질 피처
    'pm10_grade': 'good',      # 15.0 ≤ 30 (좋음)
    'mask_needed': False,      # 15.0 ≤ 50
    'outdoor_activity_ok': True, # 15.0 ≤ 80

    # 종합 지수
    'comfort_score': 18.0      # 계산 과정은 아래 참조
}
```

### 쾌적지수 계산 과정 (상세):

```python
# 1단계: 기본 점수
base_score = 50.0

# 2단계: 기온 점수 (-2.5°C)
temp_score = 10  # -2.5 < 0 (극한 온도)

# 3단계: 기온 반영 (50% 비중)
score = base_score * 0.5 + temp_score * 0.5
score = 50 * 0.5 + 10 * 0.5 = 30.0

# 4단계: 미세먼지 점수 (15.0 μg/m³)
pm10_score = 90  # 15.0 ≤ 15 (매우 좋음)

# 5단계: 미세먼지 반영 (30% 비중)
score = score * 0.7 + pm10_score * 0.3
score = 30 * 0.7 + 90 * 0.3 = 21 + 27 = 48.0

# 6단계: 보정 적용
score -= (True * 10)    # 출퇴근시간 -10점 = 38.0
score += (False * 5)    # 주말 아님 +0점 = 38.0
score -= (True * 20)    # 극한기온 -20점 = 18.0

# 7단계: 범위 제한 (0-100)
final_score = max(0, min(100, 18.0)) = 18.0
```

## 🛠️ 코드에서 확인할 수 있는 주요 함수

### 1. `create_ml_dataset()` - 메인 변환 함수
```python
# 위치: src/features/feature_builder.py:10-155
# 역할: 원시 데이터를 받아 기본 피처 추출 후 엔지니어링 적용
raw_data = {...}  # 원시 데이터
ml_dataset = create_ml_dataset(raw_data)
```

### 2. `add_engineered_features()` - 피처 엔지니어링
```python
# 위치: src/features/feature_builder.py:157-249
# 역할: 기본 피처를 받아 21개 엔지니어링 피처 추가
basic_df = pd.DataFrame(...)
enhanced_df = add_engineered_features(basic_df)
```

### 3. `calculate_comfort_score()` - 쾌적지수 계산
```python
# 위치: src/features/feature_builder.py:252-296
# 역할: 기상 조건을 종합하여 0-100점 쾌적지수 계산
scores = calculate_comfort_score(df)
```

## 🔧 개발자를 위한 참고사항

### 피처 추가 시 고려사항:
1. **결측치 처리**: `-9`, `-99`, `-999` 등은 결측치로 처리
2. **데이터 타입**: 범주형/수치형 구분하여 적절한 변환 적용
3. **스케일링**: 수치형 피처는 범위가 다르므로 정규화 고려
4. **상관관계**: 새 피처가 기존 피처와 높은 상관관계가 없는지 확인

### 성능 최적화:
- `pd.cut()` 사용으로 구간 분류 효율화
- `map()` 함수로 조건부 변환 벡터화
- `isin()` 메서드로 멤버십 테스트 최적화