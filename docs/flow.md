# MLOps 파이프라인 플로우 문서

## 📋 개요

날씨 데이터 기반 쾌적지수 예측 모델의 완전한 MLOps 파이프라인입니다.
S3에서 데이터를 로드하고, 전처리, 모델 학습, 평가 후 최고 성능 모델을 S3에 저장하는 자동화된 워크플로우를 제공합니다.

## 🔄 전체 플로우

```
S3 데이터 로드 → 데이터 전처리 → 모델 학습 → 성능 평가 → 최고 모델 선택 → S3 저장 → WANDB 추적
```

## 📁 핵심 파일 구조

```
src/
├── data/
│   └── s3_pull_processed.py    # S3에서 전처리된 데이터 로드
├── models/
│   ├── split.py               # 데이터 분할 및 스케일링
│   ├── train.py               # 모델 학습 및 평가
│   └── # tune.py                # 하이퍼파라미터 튜닝 -> 예정. 아직 진행 안 함. 
└── utils/
    └── utils.py               # 공통 유틸리티 함수
```

## 🔍 상세 플로우 설명

### 1️⃣ 데이터 로드 단계

**파일**: `src/data/s3_pull_processed.py`

**목적**: S3에서 전처리된 날씨 데이터를 로드

**S3 입력**:
- 버킷: `weather-mlops-team-data`
- 키: `ml_dataset/weather_features_full.csv`
- 설명: 피처 엔지니어링이 완료된 날씨 데이터

**주요 기능**:
```python
def get_processed_data():
    # S3 클라이언트 생성 (환경변수 기반)
    # 전처리된 CSV 파일 다운로드
    # DataFrame으로 변환하여 반환
```

**환경변수 의존성**:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY` 
- `AWS_REGION`
- `S3_BUCKET`

### 2️⃣ 데이터 전처리 단계

**파일**: `src/models/split.py`

**목적**: 데이터 정제, 분할, 스케일링

**입력**: `get_processed_data()`에서 로드된 DataFrame

## 🔬 split.py 코드 작성 근거

**분석 노트북**: `notebooks/split_practice (1).ipynb`

### 데이터 탐색 결과:
- **데이터 크기**: 342,500개 행, 34개 컬럼
- **타겟 변수**: `comfort_score` (4.5~91.5, 평균 64.5)
- **피처 개수**: 30개 (타겟, pm10, datetime, station_id 제외)

### 결측치 패턴 발견:
```
=== 의심스러운 값들 (결측치일 가능성) ===
temperature: -99 값이 23개 (0.0%)
temperature: -9 값이 108개 (0.0%)
wind_speed: -9 값이 325개 (0.1%)
humidity: -9 값이 1,577개 (0.5%)
pressure: -9 값이 42개 (0.0%)
rainfall: -9 값이 307,928개 (89.9%)  # 고결측 컬럼!
wind_direction: -9 값이 325개 (0.1%)
dew_point: -99 값이 1,585개 (0.5%)
dew_point: -9 값이 437개 (0.1%)
cloud_amount: -9 값이 371개 (0.1%)
visibility: -9 값이 6,795개 (2.0%)
sunshine: -9 값이 150,933개 (44.1%)  # 고결측 컬럼!
temp_comfort: -99 값이 23개 (0.0%)
temp_comfort: -9 값이 108개 (0.0%)
```

### 스케일 차이 문제:
| 피처명          | 최소값   | 최대값    | 평균      | 표준편차   |
|-----------------|---------|----------|----------|-----------| 
| temperature     | -99.00  | 37.70    | 14.66    | 10.67     |
| visibility      | -9.00   | 28,020.12| 2,802.12 | 1,619.49  | # 큰 스케일!
| pressure        | -9.00   | 1,039.50 | 1,015.15 | 13.97     | # 큰 스케일!
| is_morning_rush | 0.00    | 1.00     | 0.12     | 0.33      | # 이진변수

### 범주형 변수 확인:
- `season`: spring, summer, winter, autumn
- `temp_category`: warm, mild, cold, very_cold, hot  
- `pm10_grade`: good, moderate, bad, very_bad
- `region`: central, southern, unknown

**주요 처리 과정**:
1. **결측치 처리**
   - `-99`, `-9` 값을 NaN으로 변환 (노트북에서 발견한 패턴)
   - 결측치 50% 이상 컬럼 제거 (`rainfall` 89.9%, `sunshine` 44.1%)
   - 나머지 수치형 결측치는 평균값으로 대체

2. **피처 엔지니어링**
   - 타겟 변수: `comfort_score` (쾌적지수) - 노트북 분석으로 확인
   - 제외 컬럼: `comfort_score`, `pm10`, `datetime`, `station_id`
   - 원핫인코딩: `season`, `temp_category`, `pm10_grade`, `region` (노트북에서 확인된 범주형 변수)

3. **데이터 분할**
   - Train/Val/Test 분할 (기본: 60%/20%/20%)
   - 시드 고정으로 재현 가능

4. **스케일링**
   - StandardScaler 적용 (노트북에서 발견한 스케일 차이 해결)
   - 학습 데이터 기준으로 fit, 검증/테스트 데이터에 transform

### 노트북 분석 결론:
```
✅ 데이터 로드: 342,500개 행, 34개 컬럼
✅ 타겟 변수: comfort_score (4.5~91.5, 평균 64.5)
✅ 피처 개수: 30개 (pm10, datetime, station_id 제외)
✅ 결측치 패턴: -99, -9가 결측치 표시
✅ 고결측 컬럼: rainfall(89.9%), sunshine(44.1%)
✅ 스케일 차이: visibility(28,020), pressure(1,039) vs 이진변수(0-1)
✅ 범주형 변수: season, temp_category, pm10_grade, region

split.py에 반영된 전처리:
✅ 결측치 처리: -99, -9 → NaN → 평균값 대체
✅ 고결측 컬럼 자동 제거: 50% 이상 결측치면 제거
✅ 범주형 원핫인코딩: drop_first=True로 다중공선성 방지
✅ 표준화: StandardScaler로 모든 피처 스케일 통일
```

**출력**: `(X_train_scaled, X_val_scaled, X_test_scaled, y_train, y_val, y_test, scaler)`

### 3️⃣ 모델 학습 단계

**파일**: `src/models/train.py`

**목적**: 다중 모델 학습, 평가, 최고 모델 선택 및 저장

**주요 기능**:

1. **실험 관리**
   - WANDB 자동 실험명 생성 (`weather-predictor-001`, `002`, ...)
   - 환경변수 기반 프로젝트 설정

2. **모델 학습**
   - 지원 모델: Linear, Ridge, Lasso, RandomForest, LightGBM, XGBoost, CatBoost
   - 각 모델별 Train/Val/Test 성능 평가
   - RMSE, MAE 지표 계산

3. **성능 추적**
   - WANDB에 모든 모델 성능 로깅
   - 실시간 실험 추적 가능

4. **최고 모델 선택**
   - Validation RMSE 기준으로 최고 성능 모델 선택
   - 선택된 모델만 S3에 저장

**S3 출력**:
- 경로: `s3://weather-mlops-team-data/models/{experiment_name}/`
- 구조:
  ```
  models/weather-predictor-XXX/
  ├── config/
  │   ├── train_config.json      # 하이퍼파라미터
  │   ├── data_info.json         # 데이터 정보
  │   └── requirements.txt       # 라이브러리 버전
  ├── metadata/
  │   ├── metrics.json           # 성능 지표
  │   └── experiment_log.json    # 실험 정보
  └── model_artifact/
      ├── model.pkl              # 학습된 모델
      └── scaler.pkl             # 전처리 객체
  ```

### 4️⃣ 유틸리티 지원

**파일**: `src/utils/utils.py`

**주요 기능**:

1. **환경 관리**
   - `.env` 파일 자동 로드
   - 시드 고정 함수 (`set_seed`)

2. **실험 관리**
   - 자동 실험명 증가 (`auto_increment_run_suffix`)
   - 프로젝트 경로 관리

3. **S3 연동**
   - S3 클라이언트 생성 (`get_s3_client`)
   - DataFrame S3 업로드 (`save_to_s3`)
   - 구조화된 모델 저장 (`save_model_to_s3`)

## 🚀 실행 방법

### 기본 실험 (전체 모델)
```bash
docker exec -it container bash -c "python /app/src/models/train.py"
```

### 특정 모델만 학습
```bash
docker exec -it container bash -c "python /app/src/models/train.py --model_names='[\"rf\", \"xgb\"]'"
```

### 데이터 분할 비율 변경
```bash
docker exec -it container bash -c "python /app/src/models/train.py --test_size=0.3 --val_size=0.15"
```

### 시드 변경
```bash
docker exec -it container bash -c "python /app/src/models/train.py --random_state=999"
```

### 하이퍼파라미터 튜닝 -> 예정. 아직 진행 안 함. 
```bash
docker exec -it container bash -c "python /app/src/models/tune.py --search_type=random"
```

## 📊 S3 데이터 플로우

### 입력 데이터
- **소스**: `s3://weather-mlops-team-data/ml_dataset/weather_features_full.csv`
- **설명**: 피처 엔지니어링 완료된 날씨 데이터
- **크기**: 342,500 샘플 × 34 피처
- **사용처**: `s3_pull_processed.py`에서 로드

### 출력 모델
- **경로**: `s3://weather-mlops-team-data/models/weather-predictor-XXX/`
- **내용**: 최고 성능 모델 + 메타데이터 + 설정 파일
- **용도**: 프로덕션 배포, 모델 버전 관리
- **생성**: `train.py`에서 자동 저장

## 🔧 환경변수 설정

**.env 파일 필수 설정**:
```bash
# AWS S3
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=ap-northeast-2
S3_BUCKET=weather-mlops-team-data

# WANDB
WANDB_API_KEY=your_wandb_api_key
WANDB_ENTITY=your_wandb_entity
WANDB_PROJECT=weather-predictor
```

## 📈 실험 추적

### WANDB 통합
- **프로젝트**: `weather-predictor`
- **실험명**: 자동 증가 (`weather-predictor-001`, `002`, ...)
- **로깅 내용**:
  - 모든 모델의 Train/Val/Test RMSE, MAE
  - 최고 모델 정보
  - 하이퍼파라미터
  - 실험 설정

### 성능 비교
- 실험별 성능 비교 가능
- 대시보드에서 시각적 분석
- 모델 선택 근거 제공

## 🎯 최고 성능 모델

**현재 최고 성능**: `weather-predictor-006`
- **모델**: Random Forest
- **Val RMSE**: 2.5325
- **Test RMSE**: 2.5351
- **특징**: 시드 변경에도 안정적 성능

## 📈 체계적인 모델 성능 평가 과정

**실험 문서**: `docs/model_test.md`

### 실험 1: 베이스라인 설정 (003번)
**목적**: 전체 모델 성능 비교 및 베이스라인 설정

**실행 코드**:
```bash
docker exec -it container bash -c "python /app/src/models/train.py"
```

**결과 분석**:
| 모델 | Val RMSE | Test RMSE | 순위 |
|------|----------|-----------|------|
| **RF** | **2.5421** | **2.5306** | 🏆 1위 |
| CAT | 2.5470 | 2.5426 | 🥈 2위 |
| XGB | 2.5723 | 2.5668 | 🥉 3위 |
| LGBM | 3.1257 | 3.1284 | 4위 |
| Linear | 3.6223 | 3.6396 | 5위 |
| Ridge | 3.6223 | 3.6396 | 5위 |
| Lasso | 4.5277 | 4.5455 | 7위 |

**핵심 발견**: 
- 🌟 **Random Forest가 최고 성능**
- 🌳 **트리 기반 모델들이 선형 모델 대비 우수**
- 📊 **선형 모델들은 RMSE 3.6+ 로 성능 부족**

### 실험 2: 트리 모델 집중 분석 (004번)
**목적**: 성능 우수한 트리 모델들만 집중 분석

**실행 코드**:
```bash
docker exec -it container bash -c "python /app/src/models/train.py --model_names='[\"rf\", \"xgb\", \"lgbm\", \"cat\"]'"
```

**결과**: 003번과 동일한 성능 (같은 데이터, 같은 시드)
- ✅ **RF 일관성 확인** - 여전히 최고 성능
- ⏱️ **학습 시간 단축** - 선형 모델 제외로 효율성 증대

### 실험 3: 데이터 분할 비율 실험 (005번)
**목적**: 더 큰 테스트셋으로 일반화 성능 확인

**실행 코드**:
```bash
docker exec -it container bash -c "python /app/src/models/train.py --model_names='[\"rf\", \"xgb\", \"cat\"]' --test_size=0.3 --val_size=0.15"
```

**데이터 분할 변경**:
- 기존: Train 60%, Val 20%, Test 20%
- 변경: Train 55%, Val 15%, Test 30%

**성능 비교 (004 vs 005)**:
| 모델 | 004 Val RMSE | 005 Val RMSE | 004 Test RMSE | 005 Test RMSE |
|------|--------------|--------------|---------------|---------------|
| RF | 2.5421 | 2.5500 | 2.5306 | 2.5422 |
| CAT | 2.5470 | 2.5525 | 2.5426 | 2.5472 |
| XGB | 2.5723 | 2.5809 | 2.5668 | 2.5723 |

**중요한 발견**:
- 🎯 **더 큰 테스트셋(30%)에서도 RF가 여전히 최고**
- 📈 **성능 안정성** - 데이터 분할 변경에도 순위 유지
- ✅ **RF의 일관성** 재확인

### 실험 4: 시드 안정성 테스트 (006번)
**목적**: 다른 랜덤 시드로 결과 재현성 및 안정성 확인

**실행 코드**:
```bash
docker exec -it container bash -c "python /app/src/models/train.py --model_names='[\"rf\", \"cat\"]' --random_state=999"
```

**시드 변경**: 42 → 999

**RF 성능 안정성 확인**:
| 시드 | Val RMSE | Test RMSE | 비고 |
|------|----------|-----------|------|
| 42 | 2.5421 | 2.5306 | 기존 |
| 999 | **2.5325** | **2.5351** | **최고 성능** |

**최종 결론**:
- 🏆 **RF가 시드에 관계없이 최고 성능 유지**
- 📊 **성능 안정성** - 시드 변경에도 비슷한 성능
- 🎯 **RF의 신뢰성** - 다양한 조건에서도 일관된 우수성

### 전체 실험 요약
```
실험 진행 과정:
001-002: 자동 번호 생성 테스트
003: 전체 모델 비교 → RF 최고
004: 트리 모델만 → RF 최고  
005: 데이터 분할 변경 → RF 최고
006: 시드 변경 → RF 최고

결론: Random Forest가 가장 안정적이고 우수한 모델! 🌟
```

### 성능 평가 기준
1. **주요 지표**: Validation RMSE (모델 선택 기준)
2. **최종 확인**: Test RMSE (실제 성능 측정)  
3. **보조 지표**: Train RMSE, MAE (오버피팅 확인)
4. **안정성**: 다양한 조건에서의 일관성

### 하이퍼파라미터 현황
**현재 상태**: 모든 모델이 기본 하이퍼파라미터 사용
- **RandomForest**: `n_estimators=100`, `max_depth=None`, `min_samples_split=2`, ...
- **XGBoost**: `n_estimators=100`, `max_depth=6`, `learning_rate=0.3`, ...
- **LightGBM**: `n_estimators=100`, `max_depth=-1`, `learning_rate=0.1`, ...

**향후 계획**: `tune.py`를 활용한 하이퍼파라미터 최적화로 성능 더 개선 예정 