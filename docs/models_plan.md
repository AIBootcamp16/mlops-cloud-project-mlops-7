
맞습니다! 

`split.py`에서는 S3 저장 안 해도 됩니다.

1. **S3에서 데이터 로드**
2. **train/validation/test 분리**
3. **정규화/표준화**
4. **메모리에서 바로 return** (train_X, train_y, val_X, val_y, test_X, test_y)

그러면 `train.py`에서 `split.py`의 함수를 호출해서 바로 받아서 학습하면 되니까, 굳이 중간 결과물을 S3에 다시 저장할 필요 없죠.

임시 데이터를 S3에 저장하는 건 비용도 들고 불필요한 I/O입니다.


네, 맞습니다!

`train.py`에서는:

1. **`split.py`에서 준비된 데이터 가져오기** (함수 호출)
2. **모델 학습** (LightGBM, XGBoost 등)
3. **학습된 모델을 로컬 또는 S3에 저장** (`.pkl`, `.joblib` 등)
4. **학습 메트릭 로깅** (wandb, 로그 파일 등)

데이터 전처리나 분할은 `split.py`에서 이미 다 처리했으니까, `train.py`는 순수하게 **모델 학습과 저장**에만 집중하면 됩니다.

깔끔한 역할 분리네요!


네, 맞습니다!
train.py에서:
여러 모델 학습 (RandomForest, LightGBM, XGBoost, CatBoost 등)
각 모델 성능 평가 (RMSE, MAE 등으로 비교)
베스트 모델 선택 (성능 지표 기준)
최고 성능 모델만 S3에 저장 (best_model.pkl)
이렇게 하면 나중에 API나 배포 단계에서 S3에서 베스트 모델만 로드해서 사용하면 되니까 효율적이죠.
실험 과정의 모든 모델을 저장할 필요 없이, 최종 선택된 하나만 저장하는 게 맞습니다.

네, `train.py`에 들어가는 게 맞습니다!

`train.py`에서:

1. **여러 모델 학습**
2. **각 모델 성능 평가** (validation set으로)
3. **베스트 모델 선택**
4. **최종 테스트 평가** (test set으로)
5. **베스트 모델 저장**

모델 학습과 평가는 한 세트니까 분리할 필요 없어요. 

만약 나중에 배포된 모델의 성능을 모니터링하거나 새로운 데이터로 재평가하는 건 별도 스크립트(`evaluate.py` 같은)로 만들면 되지만, 학습 과정에서의 평가는 `train.py`에 포함되는 게 자연스럽습니다.


----

네, 맞습니다! wandb 설정과 네이밍 규칙은 보통 이렇게 관리해요:
1. 설정 파일로 관리:
config/wandb_config.yaml 또는 config.py에 프로젝트명, 실험명 규칙 저장
버전 관리 (v01, v02...)는 자동 증가 또는 수동 설정
2. 환경변수로 관리:
.env 파일에 WANDB_PROJECT, WANDB_ENTITY 등 저장
버전은 날짜 기반 (20241201_v01) 또는 Git 해시 활용
3. utils 함수로 관리:
src/utils/utils.py에 get_experiment_name() 같은 함수 만들어서
자동으로 버전 번호 증가하는 로직 구현
4. train.py에서 직접 관리:
실험 시작할 때 wandb.init()에서 run_name 설정
날짜+모델명+버전 조합 (예: "20241201_lightgbm_v01")
보통 config 파일 + utils 함수 조합을 많이 써요. 이미 src/utils/utils.py에 auto_increment_run_suffix() 함수가 있으니까 그걸 활용하면 될 것 같네요!

좋은 지적이에요! 모델 설정값 저장 방법은 여러 가지가 있어요:

**1. 모델과 함께 저장:**
- `joblib.dump({'model': best_model, 'params': best_params, 'scaler': scaler}, 'model_package.pkl')`
- 모델, 하이퍼파라미터, 전처리 객체를 하나의 패키지로 저장

**2. 별도 메타데이터 파일:**
- `model_metadata.json` 또는 `model_config.yaml`로 S3에 함께 저장
- 모델 파일과 같은 경로에 설정값만 따로 저장

**3. MLflow 스타일:**
- `model/` 폴더 안에 `model.pkl` + `MLmodel` + `conda.yaml` 구조
- 모델, 설정, 의존성을 폴더 단위로 관리

**4. wandb artifact 활용:**
- wandb에서 모델을 artifact로 저장하면 자동으로 메타데이터 포함
- 나중에 wandb에서 모델 + 설정 함께 다운로드 가능

보통 **1번(패키지로 저장)** 또는 **2번(메타데이터 분리)**를 많이 써요. 이미 wandb 쓰신다면 **4번**이 가장 깔끔할 것 같네요!


---
아, 멘토님이 **메타데이터 추적**을 강조하신 거네요!

그러면:

**1. wandb에서 자동 메타데이터 추적:**
- `wandb.config.update(hyperparams)` 로 하이퍼파라미터 로깅
- `wandb.log_model()` 로 모델 저장하면 자동으로 config도 함께 저장됨

**2. 모델 저장 시 메타데이터 포함:**
```python
model_info = {
    'model': best_model,
    'hyperparameters': best_params,
    'metrics': best_scores,
    'training_date': datetime.now(),
    'data_version': 'v01',
    'scaler': scaler
}
```

**3. S3 객체 메타데이터 활용:**
- S3에 저장할 때 객체의 metadata 필드에 하이퍼파라미터 정보 추가
- 나중에 모델 로드할 때 메타데이터도 함께 조회 가능

멘토님 조언은 **모델과 설정이 분리되지 않고 하나의 정보 단위로 추적되어야 한다**는 뜻 같아요. wandb artifact가 이런 요구사항에 가장 적합할 것 같네요!

----
`fire`는 Python 함수나 클래스를 **커맨드라인 인터페이스(CLI)**로 자동 변환해주는 라이브러리예요.

즉, `python split.py`, `python train.py` 같이 **각 스크립트를 개별적으로 실행**할 수 있게 해주고, 함수의 파라미터들을 **커맨드라인 인자**로 받을 수 있게 해줍니다.

예를 들어:
- `python train.py --model_type=lightgbm --n_estimators=100`
- `python split.py --test_size=0.2 --random_state=42`

이런 식으로 **각 단계를 독립적으로 실행하면서 파라미터도 유연하게 조정**할 수 있어요. MLOps 파이프라인에서 각 단계를 따로따로 돌리거나 디버깅할 때 매우 유용합니다.

---
**설치:** `requirements.txt`에 `fire==0.5.0` 추가하고 `pip install fire`

**사용할 파일들:**
- `split.py` - 데이터 분할 함수를 CLI로
- `train.py` - 모델 학습 함수를 CLI로  
- `data_cleaning.py` - 전처리 함수를 CLI로

**사용 방법:**
각 파일 맨 아래에 `fire.Fire()` 추가하면 끝!

```python
import fire

def my_function(param1, param2=default_value):
    # 함수 내용
    pass

if __name__ == "__main__":
    fire.Fire()  # 이 한 줄만 추가하면 CLI 완성
```

그러면 `python split.py --param1=value --param2=value` 이런 식으로 실행 가능해요.

**언제 설치:** 지금 당장! 각 모듈을 개별 실행하려면 필요하니까 `split.py` 작성하기 전에 설치하는 게 좋아요.

==========================================================

# 참고 코드 (콘텐츠 추천 모델 만들기)

## Dataset - watch_log

- 데이터셋 관련 기능 구현
    - **데이터셋 준비** → 모델 준비 → 학습 → 검증 및 평가 → 모델 저장

### 데이터셋 준비

src/dataset/watch_log.py

```
import os

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder

from src.utils.utils import project_path


class WatchLogDataset:
    def __init__(self, df, scaler=None, label_encoder=None):
        self.df = df
        self.features = None
        self.labels = None
        self.scaler = scaler
        self.label_encoder = label_encoder
        self.contents_id_map = None
        self._preprocessing()

    def _preprocessing(self):
        # content_id를 정수형으로 변환
        if self.label_encoder:
            self.df["content_id"] = self.label_encoder.transform(self.df["content_id"])
        else:
            self.label_encoder = LabelEncoder()
            self.df["content_id"] = self.label_encoder.fit_transform(self.df["content_id"])
        
        # content_id 디코딩 맵 생성
        self.contents_id_map = dict(enumerate(self.label_encoder.classes_))

        # 타겟 및 피처 정의
        target_columns = ["rating", "popularity", "watch_seconds"]
        self.labels = self.df["content_id"].values
        features = self.df[target_columns].values

        # 피처 스케일링
        if self.scaler:
            self.features = self.scaler.transform(features)
        else:
            self.scaler = StandardScaler()
            self.features = self.scaler.fit_transform(features)

    def decode_content_id(self, encoded_id):
        return self.contents_id_map[encoded_id]

    @property
    def features_dim(self):
        return self.features.shape[1]

    @property
    def num_classes(self):
        return len(self.label_encoder.classes_)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.features[idx], self.labels[idx]


def read_dataset():
    watch_log_path = os.path.join(project_path(), "dataset", "watch_log.csv")
    return pd.read_csv(watch_log_path)


def split_dataset(df):
    train_df, val_df = train_test_split(df, test_size=0.2, random_state=42)
    train_df, test_df = train_test_split(train_df, test_size=0.2, random_state=42)
    return train_df, val_df, test_df


def get_datasets(scaler=None, label_encoder=None):
    df = read_dataset()
    train_df, val_df, test_df = split_dataset(df)
    train_dataset = WatchLogDataset(train_df, scaler, label_encoder)
    val_dataset = WatchLogDataset(val_df, scaler=train_dataset.scaler, label_encoder=train_dataset.label_encoder)
    test_dataset = WatchLogDataset(test_df, scaler=train_dataset.scaler, label_encoder=train_dataset.label_encoder)
    return train_dataset, val_dataset, test_dataset

```

###Dataset - data_loader

- 데이터 로더 기능 구현 - ML 학습 시 필요한 데이터셋을 다양한 형태로 다루기 위한 기능
    - **데이터셋 준비** → 모델 준비 → 학습 → 검증 및 평가 → 모델 저장

### 데이터셋 준비

src/dataset/data_loader.py

```
import math

import numpy as np


class SimpleDataLoader:
    def __init__(self, features, labels, batch_size=32, shuffle=True):
        self.features = features
        self.labels = labels
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.num_samples = len(features)
        self.indices = np.arange(self.num_samples)

    def __iter__(self):
        if self.shuffle:
            np.random.shuffle(self.indices)
        self.current_idx = 0
        return self

    def __next__(self):
        if self.current_idx >= self.num_samples:
            raise StopIteration

        start_idx = self.current_idx
        end_idx = start_idx + self.batch_size
        self.current_idx = end_idx

        batch_indices = self.indices[start_idx:end_idx]
        return self.features[batch_indices], self.labels[batch_indices]
        
    def __len__(self):
        return math.ceil(self.num_samples / self.batch_size)
```

## Model

- 모델 아키텍처 정의 및 학습 알고리즘 구현
    - 데이터셋 준비 ****→ **모델 준비** → 학습 → 검증 및 평가 → 모델 저장

### 모델 준비

src/model/movie_predictor.py

```
import numpy as np


class MoviePredictor:
    name = "movie_predictor"

    def __init__(self, input_dim, hidden_dim, num_classes):
        self.weights1 = np.random.randn(input_dim, hidden_dim) * 0.01
        self.bias1 = np.zeros((1, hidden_dim))
        self.weights2 = np.random.randn(hidden_dim, num_classes) * 0.01
        self.bias2 = np.zeros((1, num_classes))

    def relu(self, x):
        return np.maximum(0, x)

    def softmax(self, x):
        exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=1, keepdims=True)

    def forward(self, x):
        self.z1 = np.dot(x, self.weights1) + self.bias1
        self.a1 = self.relu(self.z1)
        self.z2 = np.dot(self.a1, self.weights2) + self.bias2
        self.output = self.softmax(self.z2)
        return self.output

    def backward(self, x, y, output, lr=0.001):
        m = len(x)

        dz2 = (output - y) / m
        dw2 = np.dot(self.a1.T, dz2)
        db2 = np.sum(dz2, axis=0, keepdims=True)

        da1 = np.dot(dz2, self.weights2.T)
        dz1 = da1 * (self.z1 > 0)
        dw1 = np.dot(x.T, dz1)
        db1 = np.sum(dz1, axis=0, keepdims=True)

        # 가중치 업데이트
        self.weights2 -= lr * dw2
        self.bias2 -= lr * db2
        self.weights1 -= lr * dw1
        self.bias1 -= lr * db1
```

## Training

- 모델 학습 루프 구현
    - 데이터셋 준비 → 모델 준비 → **학습** → 검증 및 평가 → 모델 저장

### 학습

```
import numpy as np


def train(model, train_loader):
    total_loss = 0
    for features, labels in train_loader:
        predictions = model.forward(features)
        labels = labels.reshape(-1, 1)
        loss = np.mean((predictions - labels) ** 2)
        
        model.backward(features, labels, predictions)

        total_loss += loss

    return total_loss / len(train_loader)
```

## Evaluation

- 모델 추론 및 평가 루프 구현
    - 데이터셋 준비 → 모델 준비 → 학습 → **검증 및 평가** → 모델 저장

### 검증 및 평가

```
import numpy as np


def evaluate(model, val_loader):
    total_loss = 0
    all_predictions = []

    for features, labels in val_loader:
        predictions = model.forward(features)
        labels = labels.reshape(-1, 1)

        loss = np.mean((predictions - labels) ** 2)
        total_loss += loss * len(features)
        
        predicted = np.argmax(predictions, axis=1)
        all_predictions.extend(predicted)  # modified

    return total_loss / len(val_loader), all_predictions
```

## Main

- 메인 진입점 구현
    - 전체 과정(데이터셋 준비 → 모델 준비 → 학습 → 검증 및 평가 → (모델 저장)) **일괄 수행**

### 일괄 수행

```
import os
import sys

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from src.dataset.watch_log import get_datasets
from src.dataset.data_loader import SimpleDataLoader
from src.model.movie_predictor import MoviePredictor
from src.utils.utils import init_seed
from src.train.train import train
from src.evaluate.evaluate import evaluate


init_seed()


if __name__ == '__main__':
    # 데이터셋 및 DataLoader 생성
    train_dataset, val_dataset, test_dataset = get_datasets()
    train_loader = SimpleDataLoader(train_dataset.features, train_dataset.labels, batch_size=64, shuffle=True)
    val_loader = SimpleDataLoader(val_dataset.features, val_dataset.labels, batch_size=64, shuffle=False)
    test_loader = SimpleDataLoader(test_dataset.features, test_dataset.labels, batch_size=64, shuffle=False)

    # 모델 초기화
    model_params = {
        "input_dim": train_dataset.features_dim,
        "num_classes": train_dataset.num_classes,
        "hidden_dim": 64
    }
    model = MoviePredictor(**model_params)

    # 학습 루프
    num_epochs = 10
    for epoch in range(num_epochs):
        train_loss = train(model, train_loader)
        val_loss, _ = evaluate(model, val_loader)
        print(f"Epoch {epoch + 1}/{num_epochs}, "
              f"Train Loss: {train_loss:.4f}, "
              f"Val Loss: {val_loss:.4f}, "
              f"Val-Train Loss : {val_loss-train_loss:.4f}")

    # 테스트
    test_loss, predictions = evaluate(model, test_loader)
    print(f"Test Loss : {test_loss:.4f}")
    print([train_dataset.decode_content_id(idx) for idx in predictions])
```


## 모델 저장하기

### pickle(pkl), torch(pth) 포맷으로 저장하기

- 데이터셋 준비 → 모델 준비 → 학습 → 검증 및 평가 → **모델 저장**

src/model/movie_predictor.py

```
import os
import pickle
import datetime

from src.utils.utils import model_dir


def model_save(model, model_params, epoch, loss, scaler, label_encoder):
    save_dir = model_dir(model.name)
    os.makedirs(save_dir, exist_ok=True)

    current_time = datetime.datetime.now().strftime("%y%m%d%H%M%S")
    dst = os.path.join(save_dir, f"E{epoch}_T{current_time}.pkl")

    save_data = {
        "epoch": epoch,
        "model_params": model_params,
        "model_state_dict": {
            "weights1": model.weights1,
            "bias1": model.bias1,
            "weights2": model.weights2,
            "bias2": model.bias2,
        },
        "loss": loss,
        "scaler": scaler,
        "label_encoder": label_encoder,
    }

    # 데이터 저장
    with open(dst, "wb") as f:
        pickle.dump(save_data, f)

    print(f"Model saved to {dst}")
```

## Fire 라이브러리를 통한 태스크 분리 및 파라미터화

- Fire 라이브러리를 활용하면 태스크별로 필요한 인자를 설정하여 CLI 기반 프로그램을 쉽고 빠르게 만들 수 있습니다.
- 태스크를 분리하면 다양한 장점이 있습니다.(필요한 태스크만 수행, 트러블 슈팅 및 디버깅 용이, 유연한 자원 할당, 유지보수성, 워크플로우 관리 등)



------------

**Fire를 사용하면 다양한 실험 설정으로 모델을 실행할 수 있어요!** 🔥

**기본 사용법:**

**1. 기본 실행 (모든 기본값 사용):**
```bash
docker exec -it mlops-cloud-project-mlops-7-jupyter-1 bash -c "python /app/src/models/train.py"
```

**2. 특정 모델들만 학습:**
```bash
# Random Forest와 XGBoost만
docker exec -it mlops-cloud-project-mlops-7-jupyter-1 bash -c "python /app/src/models/train.py --model_names='[\"rf\", \"xgb\"]'"

# 선형 모델들만
docker exec -it mlops-cloud-project-mlops-7-jupyter-1 bash -c "python /app/src/models/train.py --model_names='[\"linear\", \"ridge\", \"lasso\"]'"
```

**3. 데이터 분할 비율 조정:**
```bash
# 테스트 30%, 검증 15%로 설정
docker exec -it mlops-cloud-project-mlops-7-jupyter-1 bash -c "python /app/src/models/train.py --test_size=0.3 --val_size=0.15"
```

**4. 랜덤 시드 변경:**
```bash
# 다른 시드로 실험
docker exec -it mlops-cloud-project-mlops-7-jupyter-1 bash -c "python /app/src/models/train.py --random_state=123"
```

**5. 복합 실험:**
```bash
# 트리 모델만, 큰 테스트셋, 다른 시드
docker exec -it mlops-cloud-project-mlops-7-jupyter-1 bash -c "python /app/src/models/train.py --model_names='[\"rf\", \"xgb\", \"lgbm\", \"cat\"]' --test_size=0.25 --random_state=999"
```

**실험 예시들:**
```bash
docker exec -it mlops-cloud-project-mlops-7-jupyter-1 bash -c "python /app/src/models/train.py --model_names='[\"rf\", \"xgb\"]' --test_size=0.25"
```


**네, 맞습니다!** 🎯

**Fire로 다른 설정으로 실행하면 새로운 실험 번호로 저장됩니다:**

- **첫 번째 실행**: `weather-predictor-001` ✅ (이미 완료)
- **두 번째 실행**: `weather-predictor-002` 
- **세 번째 실행**: `weather-predictor-003`
- **...계속 증가**

**예를 들어:**
```bash
# 이 명령어를 실행하면
docker exec -it mlops-cloud-project-mlops-7-jupyter-1 bash -c "python /app/src/models/train.py --model_names='[\"rf\", \"xgb\"]'"

# 결과:
# - WANDB: weather-predictor-002 실험으로 기록
# - S3: s3://weather-mlops-team-data/models/weather-predictor-002/ 에 저장
```

**이렇게 되는 이유:**
- `utils.py`의 `auto_increment_run_suffix("weather-predictor")` 함수가 자동으로 번호를 증가시킴
- 매번 실행할 때마다 새로운 실험으로 관리됨

**장점:**
- 🔄 **실험 버전 관리** - 각 실험이 독립적으로 저장
- 📊 **성능 비교** - WANDB에서 002 vs 001 성능 비교 가능  
- 💾 **모델 보관** - 각 실험의 최고 모델이 별도 저장
- 🚀 **재현 가능성** - 언제든 특정 실험 설정으로 돌아갈 수 있음

**실험해보고 싶으시면 말씀해주세요!** 어떤 설정으로 테스트해볼까요? 🤔



**일반적인 MLOps 실험 관리 방식은 이렇습니다:**

**🔄 실험 관리 패턴:**

**1. 개발/탐색 단계:**
- 다양한 설정으로 여러 실험 실행
- 성능 비교하여 최적 설정 찾기
- 각 실험은 별도 버전으로 저장

**2. 프로덕션 단계:**
- 최고 성능 모델을 "운영 모델"로 선택
- 해당 모델만 실제 서비스에 배포

**일반적인 실험 워크플로우:**

```bash
# 실험 1: 모든 모델 비교 (기본)
python train.py  # → weather-predictor-001

# 실험 2: 트리 모델만 집중 분석
python train.py --model_names='["rf", "xgb", "lgbm", "cat"]'  # → 002

# 실험 3: 데이터 분할 비율 변경
python train.py --test_size=0.3 --val_size=0.15  # → 003

# 실험 4: 특정 시드로 재현성 확인
python train.py --random_state=999  # → 004
```

**🎯 목적별 실험:**
- **베이스라인**: 모든 모델로 전체 성능 파악
- **모델 선택**: 특정 모델군 집중 분석  
- **데이터 민감도**: 분할 비율 변경 실험
- **재현성**: 다른 시드로 안정성 확인

**💡 실제 업무에서는:**
- 10-20개 실험 후 최고 성능 모델 선택
- 해당 모델을 API 서버에 배포
- 정기적으로 새 데이터로 재학습

**어떤 실험을 해보고 싶으세요?** 🤔

--------
**네, 정확히 맞습니다!** 👍

**실제 워크플로우:**

**1. 실험 누적:**
- 001: 전체 모델 비교 → Val RMSE 2.54
- 002: 트리 모델만 → Val RMSE 2.48  
- 003: 데이터 분할 변경 → Val RMSE 2.51
- 004: 다른 시드 → Val RMSE 2.52
- 005: 특정 하이퍼파라미터 → Val RMSE **2.31** ⭐
- 006: 또 다른 설정 → Val RMSE 2.45
- ...
- 010: 마지막 실험 → Val RMSE 2.38

**2. WANDB에서 전체 비교:**
- 001~010 모든 실험을 테이블로 정렬
- `best_val_rmse` 기준으로 순위 매김
- **005번이 2.31로 최고 성능** 확인

**3. 최종 결정:**
**"005번 모델(`weather-predictor-005`)을 프로덕션에 사용하세요"**

**4. 실제 사용:**
```bash
# S3에서 005번 모델 로드
s3://weather-mlops-team-data/models/weather-predictor-005/model_artifact/model.pkl
```

**💡 핵심:**
- **실험은 계속 쌓임** (001~010...)
- **성능 비교 후 최고 버전 선택** (005)
- **나머지는 백업용으로 보관** (롤백 가능)
- **새로운 실험은 011부터 계속**

**바로 이런 방식이 맞습니다!** 🎯

---

**하이퍼파라미터 튜닝은 보통 이 단계에서 합니다!** 🎯

**📈 실험 순서 (일반적인 MLOps 워크플로우):**

**1단계: 베이스라인 설정** ✅ (완료)
- 기본 설정으로 모든 모델 비교
- 어떤 모델이 가장 유망한지 파악

**2단계: 데이터/설정 실험** (지금 단계)
- 데이터 분할 비율 변경
- 피처 엔지니어링 실험
- 전처리 방법 변경

**3단계: 하이퍼파라미터 튜닝** ⭐ (다음 단계)
- **유망한 모델 1-2개만 선택** (RF, XGB 등)
- 각 모델의 하이퍼파라미터 최적화
- GridSearch, RandomSearch, Optuna 등 사용

**4단계: 앙상블/고급 기법**
- 최고 모델들 앙상블
- 스태킹, 블렌딩 등

**🔧 하이퍼파라미터 튜닝 시점:**
- **현재**: RF가 최고 성능 (2.54 RMSE)
- **다음**: RF의 `n_estimators`, `max_depth`, `min_samples_split` 등 튜닝
- **그 다음**: XGB의 `learning_rate`, `max_depth`, `n_estimators` 등 튜닝

**💡 이유:**
- 모든 모델을 튜닝하면 시간이 너무 오래 걸림
- 유망한 모델만 집중 투자하는 게 효율적
- 베이스라인 대비 얼마나 개선되는지 측정 가능

**지금은 2-3개 기본 실험 더 하고, 그 다음에 하이퍼파라미터 튜닝하는 게 좋겠어요!** 🚀

