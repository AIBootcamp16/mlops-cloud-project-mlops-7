
import os
import random

import numpy as np


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
    return os.path.join(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            )
        )
    )

def data_dir(subdirectory=None):
    """데이터 디렉토리 경로"""
    if subdirectory:
        return os.path.join(project_path(), "data", subdirectory)
    return os.path.join(project_path(), "data")


def config_dir():
    """설정 디렉토리 경로"""
    return os.path.join(project_path(), "src", "config")

def model_dir(model_name):
    """모델 저장 디렉토리 경로"""
    return os.path.join(project_path(), "models", model_name)

def ensure_dir(path):
    """디렉토리 없으면 생성"""
    os.makedirs(path, exist_ok=True)
    return path

def auto_increment_run_suffix(name: str, pad=3):
    """실행 번호 자동 증가"""
    suffix = name.split("-")[-1]
    next_suffix = str(int(suffix) + 1).zfill(pad)
    return name.replace(suffix, next_suffix)

if __name__ == "__main__":
    set_seed(42)
    print(f"프로젝트 루트: {project_path()}")
    print(f"데이터 디렉토리: {data_dir()}")
    print(f"원시 데이터: {data_dir('raw')}")
    print(f"설정 디렉토리: {config_dir()}")
    print(f"모델 디렉토리: {model_dir('lgbm-v1')}")
    print(f"다음 실행: {auto_increment_run_suffix('experiment-001')}")