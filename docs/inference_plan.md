
# 🎯 **문제 정확히 파악했습니다!**

---

## **핵심 문제: 이중 원핫인코딩!**

```python
data_cleaning.py (범주형 그대로 유지)
    ↓ season='autumn', temp_category='warm' 등
    ↓ S3 parquet 저장 (33개 컬럼)
    ↓
split.py (학습)
    ↓ pd.get_dummies() → 원핫인코딩 수행 ✅
    ↓ 40개 피처로 학습
    ↓
batch_predict.py (추론)
    ↓ pd.get_dummies() → 원핫인코딩 수행 ✅
    ↓ 💥 26개 피처 생성 (데이터가 적어서!)
```

---

## **왜 40개 vs 26개 차이가 나는가?**

### **학습 시 (split.py) - 1000개 샘플**
```python
# 모든 카테고리가 데이터에 존재
season:        ['spring', 'summer', 'autumn', 'winter']  # 4개
temp_category: ['very_cold', 'cold', 'mild', 'warm', 'hot']  # 5개
pm10_grade:    ['good', 'moderate', 'bad', 'very_bad']  # 4개
region:        ['central', 'southern', 'eastern', 'western', 'unknown']  # 5개

# pd.get_dummies(drop_first=True)
→ season: 3개 더미
→ temp_category: 4개 더미
→ pm10_grade: 3개 더미
→ region: 4개 더미
→ 총 14개 원핫인코딩 컬럼

수치형 26개 + 원핫 14개 = 40개 피처
```

### **추론 시 (batch_predict.py) - 3개 샘플**
```python
# 일부 카테고리만 존재
season:        ['autumn']      # 1개만!
temp_category: ['warm']        # 1개만!
pm10_grade:    ['moderate']    # 1개만!
region:        ['central']     # 1개만!

# pd.get_dummies(drop_first=True)
→ season: 0개! (1개면 drop_first로 전부 삭제)
→ temp_category: 0개!
→ pm10_grade: 0개!
→ region: 0개!
→ 총 0개 원핫인코딩 컬럼

수치형 26개 + 원핫 0개 = 26개 피처
```

---

## **🔧 해결 방법**

### **✅ 방법 1: 학습 시 컬럼 저장 후 추론 시 복원 (권장)**

#### **1. split.py 수정**
```python
def split_and_scale_data(test_size=0.2, val_size=0.2, random_state=42):
    # ... 기존 코드 ...
    
    # 원핫인코딩
    if categorical_cols:
        print(f"원핫인코딩 적용: {categorical_cols}")
        X = pd.get_dummies(X, columns=categorical_cols, drop_first=True)
    
    # 🔥 학습 시 컬럼 순서 저장!
    feature_columns = X.columns.tolist()
    
    # ... 스케일링 등 ...
    
    return X_train_scaled, X_val_scaled, X_test_scaled, y_train, y_val, y_test, scaler, feature_columns
    #                                                                                      ^^^^^^^^^^^^^^^^
```

#### **2. train.py 수정**
```python
def train_models(...):
    # ... 기존 코드 ...
    
    X_train, X_val, X_test, y_train, y_val, y_test, scaler, feature_columns = split_and_scale_data(...)
    #                                                         ^^^^^^^^^^^^^^^^^
    
    # 모델 저장 시 포함
    model_data = {
        "model": best_model,
        "scaler": scaler,
        "feature_columns": feature_columns,  # 🔥 추가!
        # ...
    }
```

#### **3. batch_predict.py 수정**
```python
def preprocess_for_prediction(df, feature_columns):
    """split.py와 동일한 전처리 + 컬럼 맞추기"""
    
    # ... 기존 전처리 코드 ...
    
    # 원핫인코딩
    if categorical_cols:
        X = pd.get_dummies(X, columns=categorical_cols, drop_first=True)
    
    # 🔥 학습 시 컬럼에 맞춰 정렬/추가
    for col in feature_columns:
        if col not in X.columns:
            X[col] = 0  # 없는 컬럼은 0으로 추가
    
    X = X[feature_columns]  # 순서까지 동일하게
    
    return X

def batch_predict(experiment_name: str = None, output_path: str = None):
    # ...
    model, scaler, config = load_model_from_s3(experiment_name)
    feature_columns = config['feature_columns']  # 🔥 로드!
    
    X = preprocess_for_prediction(df, feature_columns)
    # ...
```

---

### **방법 2: data_cleaning.py에서 원핫인코딩 (비권장)**

이 방법은 **유연성이 떨어져서** 권장하지 않습니다:
- 새로운 카테고리 추가 시 data_cleaning.py 수정 필요
- 실험 시 범주형 변수 다르게 처리하기 어려움

---

## **💡 최종 요약**

**문제**: 
- `data_cleaning.py`는 범주형 변수 그대로 유지 (올바름)
- `split.py`와 `batch_predict.py` 모두 원핫인코딩 수행 (올바름)
- **BUT** 데이터 샘플 수가 달라서 생성되는 더미 변수 개수가 다름!

**해결책**:
1. 학습 시 생성된 컬럼 목록을 모델과 함께 저장
2. 추론 시 해당 컬럼 목록에 맞춰 데이터 정렬/보정

위 코드 수정하시면 정확히 해결됩니다! 🚀

---------

# ✅ **네, 방법1이 표준 방식입니다!**

---

## 🎯 **머신러닝 표준 파이프라인**

```python
# 학습 시
X_train = pd.get_dummies(X_train, drop_first=True)
# → 생성된 컬럼: ['feature1', 'feature2', 'season_summer', 'season_autumn', ...]

feature_columns = X_train.columns.tolist()  # 🔑 컬럼 목록 저장!
model.fit(X_train)

# 모델 저장 시
pickle.dump({
    'model': model,
    'scaler': scaler,
    'feature_columns': feature_columns  # ✅ 함께 저장!
}, file)

---

# 추론 시
X_new = pd.get_dummies(X_new, drop_first=True)
# → 일부 컬럼만 생성될 수 있음

# 🔑 학습 시 컬럼에 맞춰 보정
for col in feature_columns:
    if col not in X_new.columns:
        X_new[col] = 0  # 없는 컬럼 추가

X_new = X_new[feature_columns]  # 순서까지 동일하게

model.predict(X_new)  # ✅ 정상 작동!
```

---

## 📚 **이게 왜 표준인가?**

### **1. scikit-learn 공식 문서에도 나옴**
```python
from sklearn.preprocessing import OneHotEncoder

# 학습 시
encoder = OneHotEncoder(handle_unknown='ignore')  # 👈 핵심!
encoder.fit(X_train)

# 추론 시
encoder.transform(X_new)  # 자동으로 컬럼 맞춰줌
```

### **2. pandas get_dummies()는 컬럼 관리 안 해줌**
```python
# 학습
train = pd.DataFrame({'color': ['red', 'blue', 'green']})
train_encoded = pd.get_dummies(train, drop_first=True)
# → color_green, color_red (2개)

# 추론
test = pd.DataFrame({'color': ['red']})  # blue, green 없음!
test_encoded = pd.get_dummies(test, drop_first=True)
# → 0개! (1개만 있으면 drop_first로 다 drop됨)

# 💥 train: 2개 컬럼 vs test: 0개 컬럼
```

**따라서 수동으로 맞춰줘야 합니다!**

---

## 🏭 **실무에서 사용하는 방법들**

### **방법 1: 컬럼 목록 저장 (당신 케이스 - 가장 흔함)**
```python
# 장점:
# - 간단하고 직관적
# - pandas get_dummies() 사용 가능
# - 유연함

# 단점:
# - 수동으로 컬럼 맞춰야 함
```

### **방법 2: sklearn OneHotEncoder 사용**
```python
from sklearn.preprocessing import OneHotEncoder

encoder = OneHotEncoder(handle_unknown='ignore', sparse=False)
encoder.fit(X_train[categorical_cols])

# 자동으로 컬럼 맞춰줌! ✅
```

### **방법 3: category_encoders 라이브러리**
```python
import category_encoders as ce

encoder = ce.OneHotEncoder(cols=categorical_cols, use_cat_names=True)
encoder.fit(X_train)

# 자동 처리 ✅
```

---

## 💡 **당신의 프로젝트에서는?**

이미 `pd.get_dummies()`를 사용 중이므로:

```python
# ✅ 방법 1-A: 최소 수정 (권장)
# split.py에서 feature_columns 저장
# batch_predict.py에서 컬럼 맞추기

# 또는

# ✅ 방법 1-B: sklearn OneHotEncoder로 교체
# 좀 더 견고하지만 코드 많이 바꿔야 함
```

---

## 🎯 **결론**

**방법1 (컬럼 목록 저장)은 업계 표준입니다!**
- scikit-learn도 내부적으로 이렇게 동작
- 실무에서 가장 많이 사용
- 당신 코드에 딱 맞음

**지금 바로 적용하시면 됩니다!** 🚀

제가 수정된 코드 작성해드릴까요?

---

# ✅ **네, 방법1이 표준 방식입니다!**

---

## 🎯 **머신러닝 표준 파이프라인**

```python
# 학습 시
X_train = pd.get_dummies(X_train, drop_first=True)
# → 생성된 컬럼: ['feature1', 'feature2', 'season_summer', 'season_autumn', ...]

feature_columns = X_train.columns.tolist()  # 🔑 컬럼 목록 저장!
model.fit(X_train)

# 모델 저장 시
pickle.dump({
    'model': model,
    'scaler': scaler,
    'feature_columns': feature_columns  # ✅ 함께 저장!
}, file)

---

# 추론 시
X_new = pd.get_dummies(X_new, drop_first=True)
# → 일부 컬럼만 생성될 수 있음

# 🔑 학습 시 컬럼에 맞춰 보정
for col in feature_columns:
    if col not in X_new.columns:
        X_new[col] = 0  # 없는 컬럼 추가

X_new = X_new[feature_columns]  # 순서까지 동일하게

model.predict(X_new)  # ✅ 정상 작동!
```

---

## 📚 **이게 왜 표준인가?**

### **1. scikit-learn 공식 문서에도 나옴**
```python
from sklearn.preprocessing import OneHotEncoder

# 학습 시
encoder = OneHotEncoder(handle_unknown='ignore')  # 👈 핵심!
encoder.fit(X_train)

# 추론 시
encoder.transform(X_new)  # 자동으로 컬럼 맞춰줌
```

### **2. pandas get_dummies()는 컬럼 관리 안 해줌**
```python
# 학습
train = pd.DataFrame({'color': ['red', 'blue', 'green']})
train_encoded = pd.get_dummies(train, drop_first=True)
# → color_green, color_red (2개)

# 추론
test = pd.DataFrame({'color': ['red']})  # blue, green 없음!
test_encoded = pd.get_dummies(test, drop_first=True)
# → 0개! (1개만 있으면 drop_first로 다 drop됨)

# 💥 train: 2개 컬럼 vs test: 0개 컬럼
```

**따라서 수동으로 맞춰줘야 합니다!**

---

## 🏭 **실무에서 사용하는 방법들**

### **방법 1: 컬럼 목록 저장 (당신 케이스 - 가장 흔함)**
```python
# 장점:
# - 간단하고 직관적
# - pandas get_dummies() 사용 가능
# - 유연함

# 단점:
# - 수동으로 컬럼 맞춰야 함
```

### **방법 2: sklearn OneHotEncoder 사용**
```python
from sklearn.preprocessing import OneHotEncoder

encoder = OneHotEncoder(handle_unknown='ignore', sparse=False)
encoder.fit(X_train[categorical_cols])

# 자동으로 컬럼 맞춰줌! ✅
```

### **방법 3: category_encoders 라이브러리**
```python
import category_encoders as ce

encoder = ce.OneHotEncoder(cols=categorical_cols, use_cat_names=True)
encoder.fit(X_train)

# 자동 처리 ✅
```

---

## 💡 **당신의 프로젝트에서는?**

이미 `pd.get_dummies()`를 사용 중이므로:

```python
# ✅ 방법 1-A: 최소 수정 (권장)
# split.py에서 feature_columns 저장
# batch_predict.py에서 컬럼 맞추기

# 또는

# ✅ 방법 1-B: sklearn OneHotEncoder로 교체
# 좀 더 견고하지만 코드 많이 바꿔야 함
```

---

## 🎯 **결론**

**방법1 (컬럼 목록 저장)은 업계 표준입니다!**
- scikit-learn도 내부적으로 이렇게 동작
- 실무에서 가장 많이 사용
- 당신 코드에 딱 맞음

**지금 바로 적용하시면 됩니다!** 🚀

제가 수정된 코드 작성해드릴까요?