## 📋 train.py 작성 계획

### **1. 기본 구조**
```python
# 필수 import
- split.py에서 데이터 가져오기
- model_example.py에서 모델 팩토리 사용
- utils.py에서 필요한 함수들 활용
- wandb + fire 설정
```

### **2. 주요 함수 구성**
```python
def train_models(
    model_names=['rf', 'lgbm', 'xgb'], 
    test_size=0.2, 
    val_size=0.2, 
    random_state=42
):
    # 1. split.py에서 데이터 로드
    # 2. 여러 모델 학습 및 평가
    # 3. 베스트 모델 선택
    # 4. S3에 저장
```

### **3. 활용할 utils.py 기능들**
- `set_seed()`: 시드 고정
- `auto_increment_run_suffix()`: wandb 실험명 자동 생성
- `save_to_s3()`: 모델 S3 저장 (새 함수 추가 필요)

### **4. wandb 설정**
```python
# 실험명 자동 생성
experiment_name = auto_increment_run_suffix("weather_comfort_v01")
wandb.init(project="weather-mlops", name=experiment_name)
```

### **5. 모델 학습 로직**
```python
models = {}
results = {}

for model_name in model_names:
    # 모델 생성 (model_example.py 활용)
    # 학습 + 검증
    # wandb 로깅
    # 결과 저장
    
# 베스트 모델 선택 (RMSE 기준)
# S3에 저장 (모델 + 메타데이터)
```

### **6. 필요한 추가 함수 (utils.py에)**
```python
def save_model_to_s3(model, metadata, bucket, key):
    # 모델 + 메타데이터를 패키지로 S3 저장
```

### **7. Fire 설정**
```python
if __name__ == "__main__":
    fire.Fire(train_models)
```

**이렇게 구성하면 약 80-100줄 정도의 깔끔한 코드가 될 것 같아요. 진행할까요?**

---

아! 이해했어요! 🎯

**수정된 계획:**

### **1. model_example.py 참조 방식**
```python
# import 말고 참조해서 비슷한 구조로 작성
# get_model() 팩토리 패턴 활용
# 회귀 모델들 (rf, lgbm, xgb, cat) 사용
```

### **2. models_plan.md 158라인 이후 참조**
- **WatchLogDataset 클래스 구조** → 우리는 split.py에서 데이터 받아옴
- **SimpleDataLoader** → 배치 처리 (필요시)
- **MoviePredictor 학습 루프** → 여러 모델 학습 루프 구조 참조
- **model_save() 함수** → S3 저장 방식 참조
- **Fire CLI 구조** → 파라미터화된 실행

### **3. 실제 구조**
```python
def train_models(model_names=['rf', 'lgbm', 'xgb']):
    # 1. split.py에서 데이터 가져오기
    # 2. 각 모델별로 학습 루프 (models_plan.md 참조)
    # 3. wandb 로깅 (utils.py auto_increment 활용)
    # 4. 베스트 모델 선택
    # 5. S3 저장 (model_save 방식 참조)
```

**models_plan.md의 학습 루프 + 모델 저장 패턴을 참조해서 우리 프로젝트에 맞게 구현하겠다는 뜻이죠?**

맞나요? 그럼 이제 코드 작성할게요!

완료! 🎉

## **train.py 주요 특징:**

### **✅ 요구사항 반영:**
1. **최소한의 코드**: 150줄, 핵심 기능만
2. **utils.py 활용**: `set_seed()`, `auto_increment_run_suffix()` 사용
3. **wandb + 자동 번호**: `weather_comfort_v01-002` 형태로 자동 생성
4. **fire 사용**: CLI 파라미터 지원
5. **S3 저장**: 베스트 모델 + 메타데이터 패키지로 저장

### **📊 models_plan.md 참조 구조:**
- **모델 팩토리**: `get_model()` 함수
- **학습 루프**: 여러 모델 순차 학습
- **평가 지표**: RMSE, MAE 계산
- **모델 저장**: 메타데이터 포함한 패키지 저장

### **🚀 실행 방법:**
```bash
# 기본 실행
python /app/src/models/train.py

# 파라미터 조정
python /app/src/models/train.py --model_names="['rf','lgbm']" --test_size=0.3
```

### **💾 저장되는 모델 패키지:**
- 모델 객체 + 스케일러 + 메트릭 + 실험명 + 타임스탬프

이제 실행해볼까요?


-------
**RF 하이퍼파라미터 튜닝 전용 `tune.py` 만들어드릴게요!** 🎯
**완성! RF 하이퍼파라미터 튜닝 전용 `tune.py` 파일이 생성되었습니다!** 🎉

**주요 기능:**
- ✅ **GridSearch & RandomSearch** 지원
- ✅ **Cross-Validation** (기본 3-fold)
- ✅ **WANDB 통합** (`rf-tune-001`, `rf-tune-002`... 형태)
- ✅ **S3 자동 저장** (최적 모델 + 메타데이터)
- ✅ **Fire CLI** 지원
- ✅ **상세한 로깅** (상위 5개 결과까지)

**실행 코드들:**

**1. 기본 GridSearch (빠른 테스트):**
```bash
docker exec -it mlops-cloud-project-mlops-7-jupyter-1 bash -c "python /app/src/models/tune.py"
```

**2. RandomSearch (더 넓은 탐색):**
```bash
docker exec -it mlops-cloud-project-mlops-7-jupyter-1 bash -c "python /app/src/models/tune.py --search_type=random --n_iter=30"
```

**3. 더 정밀한 GridSearch:**
```bash
docker exec -it mlops-cloud-project-mlops-7-jupyter-1 bash -c "python /app/src/models/tune.py --cv_folds=5"
```

**어떤 방식으로 시작해보시겠어요?** 

**개인적으로는 2번(RandomSearch)을 추천합니다!** 더 넓은 범위를 빠르게 탐색할 수 있어요! 🚀
