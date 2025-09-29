import os
import random

import numpy as np
import boto3
from io import StringIO

# .env 파일 로드 (S3 환경변수 자동 인식용)
from dotenv import load_dotenv
load_dotenv()

def set_seed(seed: int = 42):
    """
    모든 랜덤 시드 고정
    
    Args:
        seed: 시드 값
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    
    # TensorFlow가 있는 경우
    try:
        import tensorflow as tf
        tf.random.set_seed(seed)
    except ImportError:
        pass
    
    # PyTorch가 있는 경우
    try:
        import torch
        torch.manual_seed(seed)
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    except ImportError:
        pass
    
    print(f"시드 {seed}로 고정 완료")


def project_path():
    """프로젝트 루트 경로 반환"""
    # src/utils/utils.py 에서 프로젝트 루트까지 2단계 위로
    return os.path.join(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            )
        )
    )


def src_dir():
    """src 디렉토리 경로"""
    return os.path.join(project_path(), "src")


def data_dir():
    """src/data 디렉토리 경로"""
    return os.path.join(src_dir(), "data")


def models_dir():
    """src/models 디렉토리 경로"""
    return os.path.join(src_dir(), "models")


def utils_dir():
    """src/utils 디렉토리 경로"""
    return os.path.join(src_dir(), "utils")


def notebooks_dir():
    """notebooks 디렉토리 경로"""
    return os.path.join(project_path(), "notebooks")


def saved_models_dir():
    """저장된 모델들 디렉토리 경로 (프로젝트 루트의 models)"""
    return os.path.join(project_path(), "models")


def tests_dir():
    """tests 디렉토리 경로"""
    return os.path.join(project_path(), "tests")


def docs_dir():
    """docs 디렉토리 경로"""
    return os.path.join(project_path(), "docs")


def api_dir():
    """api 디렉토리 경로"""
    return os.path.join(project_path(), "api")


def model_save_path(model_name: str):
    """모델 저장 경로"""
    return os.path.join(saved_models_dir(), model_name)


def ensure_dir(path: str):
    """디렉토리 없으면 생성"""
    os.makedirs(path, exist_ok=True)
    return path


def auto_increment_run_suffix(latest: str | None, *, default_prefix: str, pad: int = 3) -> str:
    if not latest:
        return f"{default_prefix}-000"
    try:
        base, num = latest.rsplit("-", 1)
        return f"{base}-{int(num)+1:0{pad}d}"
    except Exception:
        # 형식이 깨져도 규칙을 이 함수가 책임지고 재정의
        return f"{default_prefix}-000"


def get_model_versions(model_name: str):
    """특정 모델의 버전 목록 반환"""
    model_path = model_save_path(model_name)
    if not os.path.exists(model_path):
        return []
    
    versions = []
    for item in os.listdir(model_path):
        if os.path.isdir(os.path.join(model_path, item)):
            versions.append(item)
    
    return sorted(versions)


def get_latest_model_version(model_name: str):
    """특정 모델의 최신 버전 반환"""
    versions = get_model_versions(model_name)
    return versions[-1] if versions else None



def save_to_s3(df, bucket, key, sep=","):
    """DataFrame을 CSV로 변환 후 S3에 업로드"""
    # 1️⃣ DataFrame → CSV 문자열 변환
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, sep=sep, encoding="utf-8")

    # 2️⃣ S3 클라이언트 생성
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION")
    )

    # 3️⃣ 업로드 실행
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=csv_buffer.getvalue()
    )
    print(f"✅ S3 업로드 완료: s3://{bucket}/{key}")


def get_s3_client():
    """S3 클라이언트 생성 (중복 제거용)"""
    return boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION")
    )

def save_model_to_s3(model_data, bucket, base_path):
    """모델을 체계적인 구조로 S3에 저장"""
    import pickle
    import json
    import tempfile
    
    s3_client = get_s3_client()
    
    # 1️⃣ JSON 파일들 저장
    files_to_save = {
        f"{base_path}/config/train_config.json": model_data.get("hyperparameters", {}),
        f"{base_path}/config/data_info.json": model_data.get("data_info", {}),
        f"{base_path}/metadata/metrics.json": model_data.get("metrics", {}),
        f"{base_path}/metadata/experiment_log.json": {
            "experiment_name": model_data.get("experiment_name"),
            "wandb_project": model_data.get("wandb_project"),
            "timestamp": model_data.get("timestamp"),
            "model_name": model_data.get("model_name")
        }
    }
    
    for key, content in files_to_save.items():
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(content, indent=2, ensure_ascii=False).encode('utf-8')
        )
    
    # 2️⃣ requirements.txt 저장
    s3_client.put_object(
        Bucket=bucket,
        Key=f"{base_path}/config/requirements.txt",
        Body=model_data.get("requirements", "").encode('utf-8')
    )
    
    # 3️⃣ 모델 객체들 저장
    artifacts = {
        "model.pkl": model_data.get("model"),
        "scaler.pkl": model_data.get("scaler")
    }
    
    for filename, obj in artifacts.items():
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as temp_file:
            pickle.dump(obj, temp_file)
            temp_filename = temp_file.name
        
        try:
            s3_client.upload_file(temp_filename, bucket, f"{base_path}/model_artifact/{filename}")
        finally:
            os.remove(temp_filename)
    
    print(f"✅ 모델 S3 저장 완료: s3://{bucket}/{base_path}/")



if __name__ == "__main__":
    set_seed(42)
    
    print("=== 디렉토리 경로 확인 ===")
    print(f"프로젝트 루트: {project_path()}")
    print(f"소스 디렉토리: {src_dir()}")
    print(f"데이터 패키지: {data_dir()}")
    print(f"모델 패키지: {models_dir()}")
    print(f"유틸 패키지: {utils_dir()}")
    print(f"노트북 디렉토리: {notebooks_dir()}")
    print(f"저장된 모델 디렉토리: {saved_models_dir()}")
    print(f"테스트 디렉토리: {tests_dir()}")
    print(f"문서 디렉토리: {docs_dir()}")
    print(f"API 디렉토리: {api_dir()}")
    
    print("\n=== 모델 관련 ===")
    print(f"LGBM 모델 저장 경로: {model_save_path('lgbm')}")
    print(f"다음 실험명: {auto_increment_run_suffix('experiment-001')}")
    print(f"버전 없는 경우: {auto_increment_run_suffix('my-model')}")
    
    print("\n=== S3 관련 ===")
    print(f"S3 클라이언트 생성: {get_s3_client}")
    print(f"DataFrame S3 저장: {save_to_s3}")
    print(f"모델 구조 S3 저장: {save_model_to_s3}")