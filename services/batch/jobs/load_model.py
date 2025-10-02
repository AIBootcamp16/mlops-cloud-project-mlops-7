import os  

import pickle
import json
from io import BytesIO

from src.utils.utils import get_s3_client


def load_model_from_s3(experiment_name: str = None, bucket: str = None):
    """S3에서 모델, 스케일러, config, feature_columns 로드"""
    if bucket is None:
        bucket = os.getenv('S3_BUCKET')
    
    if experiment_name is None:
        experiment_name = os.getenv('CHAMPION_MODEL', 'default_experiment')
    
    s3_client = get_s3_client()
    
    # 모델 로드
    model_key = f"models/{experiment_name}/model_artifact/model.pkl"
    model_obj = s3_client.get_object(Bucket=bucket, Key=model_key)
    model = pickle.load(BytesIO(model_obj['Body'].read()))
    
    # 스케일러 로드
    scaler_key = f"models/{experiment_name}/model_artifact/scaler.pkl"
    scaler_obj = s3_client.get_object(Bucket=bucket, Key=scaler_key)
    scaler = pickle.load(BytesIO(scaler_obj['Body'].read()))
    
    # config 로드
    config_key = f"models/{experiment_name}/config/train_config.json"
    config_obj = s3_client.get_object(Bucket=bucket, Key=config_key)
    config = json.load(config_obj['Body'])
    
    # feature_columns 로드
    feature_col_key = f"models/{experiment_name}/config/feature_columns.json"
    feature_col_obj = s3_client.get_object(Bucket=bucket, Key=feature_col_key)
    feature_columns = json.load(feature_col_obj['Body'])
    
    return model, scaler, config, feature_columns