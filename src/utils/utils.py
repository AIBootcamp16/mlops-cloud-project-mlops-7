import os
import random

import numpy as np
import boto3
from io import StringIO

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


def auto_increment_run_suffix(name: str, pad: int = 3):
    """실행 번호 자동 증가"""
    suffix = name.split("-")[-1]
    try:
        next_suffix = str(int(suffix) + 1).zfill(pad)
        return name.replace(suffix, next_suffix)
    except ValueError:
        # 숫자가 아닌 경우 001부터 시작
        return f"{name}-001"


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