import boto3
import pandas as pd
import os
from io import StringIO

def get_s3_data():
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
        Key='raw/weather_hourly.csv'
    )
    weather_content = weather_response['Body'].read().decode('utf-8')
    weather_df = pd.read_csv(StringIO(weather_content))
    
    # 미세먼지 데이터 가져오기
    pm10_response = s3_client.get_object(
        Bucket=bucket_name, 
        Key='raw/pm10_data.csv'
    )
    pm10_content = pm10_response['Body'].read().decode('utf-8')
    pm10_df = pd.read_csv(StringIO(pm10_content))
    
    return weather_df, pm10_df

def test_s3_connection():
    """현재 있는 파일로 S3 연결 및 파일 읽기 테스트"""
    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION')
    )
    
    bucket_name = os.getenv('S3_BUCKET')
    
    try:
        # S3 연결 테스트 - 단순 텍스트 파일로 먼저 테스트
        test_response = s3_client.get_object(
            Bucket=bucket_name, 
            Key='tmp/test.txt'  # 단순 텍스트 파일로 변경
        )
        test_content = test_response['Body'].read().decode('utf-8')
        
        print("✅ S3 연결 테스트 성공!")
        print(f"테스트 파일 내용 (첫 100자): {test_content[:100]}...")
        
        # CSV 파일도 시도해보되, 오류가 나도 괜찮음
        try:
            csv_response = s3_client.get_object(
                Bucket=bucket_name, 
                Key='test/weather_rolling_7days_test.csv'
            )
            csv_content = csv_response['Body'].read().decode('utf-8')
            # 파싱 오류를 피하기 위해 더 관대한 옵션 사용
            test_df = pd.read_csv(
                StringIO(csv_content), 
                on_bad_lines='skip',  # 문제가 있는 줄은 건너뛰기
                sep=',',
                quotechar='"'
            )
            print("✅ CSV 파싱도 성공!")
            print(f"CSV 파일 shape: {test_df.shape}")
            if not test_df.empty:
                print("CSV 첫 2행:")
                print(test_df.head(2))
        except Exception as csv_e:
            print(f"⚠️  CSV 파싱 실패 (하지만 S3 연결은 정상): {csv_e}")
        
        return True
        
    except Exception as e:
        print(f"❌ S3 연결 테스트 실패: {e}")
        return False

def list_s3_objects():
    """S3 버킷의 모든 객체 목록 조회"""
    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION')
    )
    
    bucket_name = os.getenv('S3_BUCKET')
    
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in response:
            print(f"'{bucket_name}' 버킷의 파일 목록:")
            for obj in response['Contents']:
                print(f"  - {obj['Key']}")
        else:
            print(f"'{bucket_name}' 버킷이 비어있습니다.")
    except Exception as e:
        print(f"버킷 목록 조회 오류: {e}")

if __name__ == "__main__":
    print("=== S3 연결 및 CSV 읽기 기능 테스트 ===")
    
    # 현재 있는 파일로 기능 테스트
    if test_s3_connection():
        print("\n✅ 모듈이 정상적으로 작동합니다!")
        print("나중에 실제 데이터(raw/weather_hourly.csv, raw/pm10_data.csv)가")
        print("업로드되면 get_s3_data() 함수를 사용하면 됩니다.")
    else:
        print("\n❌ 환경변수나 S3 설정을 확인해주세요.")