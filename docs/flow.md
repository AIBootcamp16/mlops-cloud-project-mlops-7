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

----

s3://weather-mlops-team-data/models/weather-predictor-006/
├── config/
│   ├── train_config.json      # RF 하이퍼파라미터 (100개 트리, max_depth=None 등)
│   ├── data_info.json         # 데이터 정보 (342K 샘플, 45 피처)
│   └── requirements.txt       # 패키지 버전 정보
├── metadata/
│   ├── metrics.json           # 성능 지표 (Val RMSE: 2.5325)
│   └── experiment_log.json    # 실험 정보 (시간, WANDB 프로젝트)
└── model_artifact/
    ├── model.pkl              # RandomForest 모델 객체
    └── scaler.pkl             # StandardScaler 객체

---
**RandomForest 하이퍼파라미터 상세 설명** 🌳

## 🔍 **핵심 파라미터 분석**

### **1️⃣ 트리 구조 관련**

#### `n_estimators: 100`
- **의미**: 랜덤 포레스트에서 생성할 **결정 트리의 개수**
- **현재값**: 100개 트리
- **영향**: 많을수록 성능 향상되지만 계산 시간 증가
- **일반적 범위**: 50~500

#### `max_depth: null`
- **의미**: 각 트리의 **최대 깊이** 제한
- **현재값**: `null` = **제한 없음** (리프까지 완전 성장)
- **영향**: 제한하면 과적합 방지, 너무 제한하면 과소적합
- **일반적 범위**: 3~20 또는 None

#### `max_features: 1.0`
- **의미**: 각 분할에서 고려할 **피처 비율**
- **현재값**: `1.0` = **모든 피처 사용** (100%)
- **일반적 설정**: 
  - `"sqrt"`: √(전체 피처 수) - 분류용 기본값
  - `"log2"`: log₂(전체 피처 수)
  - `1.0`: 모든 피처 - 회귀용 기본값

### **2️⃣ 분할 조건 관련**

#### `min_samples_split: 2`
- **의미**: 노드를 분할하기 위한 **최소 샘플 수**
- **현재값**: 2개 (최소값)
- **영향**: 클수록 과적합 방지, 작을수록 세밀한 분할

#### `min_samples_leaf: 1`
- **의미**: 리프 노드에 필요한 **최소 샘플 수**
- **현재값**: 1개 (최소값)
- **영향**: 클수록 일반화 성능 향상

#### `min_impurity_decrease: 0.0`
- **의미**: 분할을 위한 **최소 불순도 감소량**
- **현재값**: 0.0 (제한 없음)
- **영향**: 클수록 보수적 분할

### **3️⃣ 샘플링 관련**

#### `bootstrap: true`
- **의미**: **부트스트랩 샘플링** 사용 여부
- **현재값**: `true` = 복원추출로 학습 데이터 생성
- **핵심**: 랜덤 포레스트의 핵심 메커니즘

#### `max_samples: null`
- **의미**: 각 트리 학습에 사용할 **최대 샘플 수**
- **현재값**: `null` = 전체 샘플 수 사용
- **영향**: 제한하면 다양성 증가

### **4️⃣ 성능 최적화**

#### `criterion: "squared_error"`
- **의미**: 분할 품질 측정 **기준**
- **현재값**: 제곱 오차 (회귀용 기본값)
- **다른 옵션**: `"absolute_error"`, `"friedman_mse"`, `"poisson"`

#### `n_jobs: null`
- **의미**: **병렬 처리** 코어 수
- **현재값**: `null` = 1개 코어 사용
- **최적화**: `-1`로 설정하면 모든 코어 사용

### **5️⃣ 기타 설정**

#### `random_state: 42`
- **의미**: **재현성**을 위한 랜덤 시드
- **현재값**: 42 (고정값)
- **중요성**: 동일한 결과 보장

#### `oob_score: false`
- **의미**: **Out-of-Bag 점수** 계산 여부
- **현재값**: `false` = 계산 안 함
- **활용**: `true`로 설정하면 검증 없이 성능 추정 가능

## 🎯 **현재 설정 분석**

### **장점** ✅
- **완전 성장**: `max_depth=null`로 복잡한 패턴 학습 가능
- **안정성**: `bootstrap=true`로 과적합 방지
- **재현성**: `random_state=42`로 일관된 결과

### **개선 가능점** 🔧
- **병렬화**: `n_jobs=-1`로 속도 향상
- **피처 다양성**: `max_features="sqrt"`로 일반화 성능 향상
- **조기 종료**: `min_samples_leaf=5` 등으로 과적합 방지

## 📊 **성능 영향도**

**높은 영향**: `n_estimators`, `max_depth`, `max_features`
**중간 영향**: `min_samples_split`, `min_samples_leaf`
**낮은 영향**: `criterion`, `bootstrap` (기본값이 최적)

**결론**: 현재는 **기본 설정**으로 안정적이지만, 하이퍼파라미터 튜닝으로 성능 개선 여지가 있습니다! 🚀

---

원본 데이터:
temperature: -10°C ~ 40°C
pressure: 980 ~ 1040 hPa
visibility: 0 ~ 28,000m

스케일링 후:
temperature: -1.5 ~ 2.1 (평균 0, 표준편차 1)
pressure: -1.8 ~ 1.9 (평균 0, 표준편차 1)  
visibility: -1.7 ~ 2.3 (평균 0, 표준편차 1)




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