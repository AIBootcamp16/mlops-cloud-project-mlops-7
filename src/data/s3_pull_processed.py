import boto3
import pandas as pd
import os
from io import StringIO

def get_processed_data():
    """S3에서 날씨 및 미세먼지 데이터를 가져와서 DataFrame으로 반환"""
    
    # S3 클라이언트 생성
    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION')
    )
    
    bucket_name = os.getenv('S3_BUCKET')
    
    # 날씨 데이터 가져오기
    weather_response = s3_client.get_object(
        Bucket=bucket_name, 
        Key='ml_dataset/weather_features_full.csv'
    )
    weather_content = weather_response['Body'].read().decode('utf-8')
    weather_df = pd.read_csv(StringIO(weather_content), low_memory=False)
    

    return weather_df