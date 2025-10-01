"""S3 Storage Client and WeatherDataS3Handler"""

import io
import json
import boto3
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional

from src.utils.logger_config import configure_logger


class S3StorageClient:
    """저수준 S3 클라이언트 (LocalStack 및 AWS S3 호환)"""

    def __init__(self, bucket_name: str, aws_access_key_id: str,
                 aws_secret_access_key: str, region_name: str,
                 endpoint_url: Optional[str] = None):
        self.bucket_name = bucket_name
        self._logger = configure_logger(self.__class__.__name__)

        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
            endpoint_url=endpoint_url,
        )

        # 버킷 확인/생성
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """버킷이 없으면 생성"""
        try:
            self.s3.head_bucket(Bucket=self.bucket_name)
            self._logger.info(f"S3 버킷 확인: {self.bucket_name}")
        except Exception:
            self._logger.warning(f"버킷 {self.bucket_name} 없음 → 새로 생성")
            self.s3.create_bucket(Bucket=self.bucket_name)

    def put_object(self, key: str, body, content_type: str = "application/octet-stream"):
        """S3에 객체 저장"""
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.s3.put_object(Bucket=self.bucket_name, Key=key, Body=body, ContentType=content_type)
        return key

    def get_object(self, key: str) -> bytes:
        """S3 객체 가져오기"""
        obj = self.s3.get_object(Bucket=self.bucket_name, Key=key)
        return obj["Body"].read()

    def list_objects(self, prefix: str = "") -> List[str]:
        """S3 객체 목록 조회"""
        resp = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
        if "Contents" not in resp:
            return []
        return [c["Key"] for c in resp["Contents"]]

    def delete_object(self, key: str):
        """S3 객체 삭제"""
        self.s3.delete_object(Bucket=self.bucket_name, Key=key)


class WeatherDataS3Handler:
    """날씨 데이터 S3 핸들러"""

    def __init__(self, s3_client: S3StorageClient):
        self.s3_client = s3_client

    def save_raw_weather_data(self, data_type: str, raw_data: str, timestamp: datetime) -> str:
        """원시 날씨 데이터 저장 (고정 경로 덮어쓰기)"""
        # 고정 경로로 항상 같은 파일에 저장
        key = f"raw/{data_type}/latest.txt"

        self.s3_client.put_object(key, raw_data, content_type="text/plain")
        print(f"원시 데이터 저장: s3://{self.s3_client.bucket_name}/{key}")
        return key

    def save_parsed_weather_data(self, data_type: str, parsed_data: List[Dict], timestamp: datetime) -> str:
        """파싱된 날씨 데이터 저장 (고정 경로 덮어쓰기)"""
        # 고정 경로로 항상 같은 파일에 저장
        key = f"processed/{data_type}/latest.json"

        json_data = json.dumps(parsed_data, ensure_ascii=False, default=str)
        self.s3_client.put_object(key, json_data, content_type="application/json")
        print(f"처리된 데이터 저장: s3://{self.s3_client.bucket_name}/{key}")
        return key

    def save_ml_dataset(self, df: pd.DataFrame, timestamp: datetime, key_suffix: str = None) -> str:
        """ML 데이터셋 저장 (고정 경로 덮어쓰기)"""
        # 고정 경로로 항상 같은 파일에 저장
        key = "ml_dataset/train/latest.parquet"

        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False)
        self.s3_client.put_object(key, buffer.getvalue(), content_type="application/octet-stream")
        print(f"ML 데이터셋 저장: s3://{self.s3_client.bucket_name}/{key}")
        return key

    def save_predict_dataset(self, df: pd.DataFrame, timestamp: datetime) -> str:
        """예측용 데이터셋 저장 (predict/ 폴더)"""
        key = "ml_dataset/predict/latest.parquet"

        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False)
        self.s3_client.put_object(key, buffer.getvalue(), content_type="application/octet-stream")
        print(f"예측 데이터셋 저장: s3://{self.s3_client.bucket_name}/{key}")
        return key

    def load_latest_ml_dataset(self, days_back: int = 7) -> Optional[pd.DataFrame]:
        """최신 ML 데이터셋 로드 (고정 경로에서)"""
        key = "ml_dataset/train/latest.parquet"

        try:
            obj = self.s3_client.get_object(key)
            print(f"📂 최신 ML 데이터셋 로드: {key}")
            return pd.read_parquet(io.BytesIO(obj))
        except Exception as e:
            print(f"❌ ML 데이터셋 로드 실패: {e}")
            return None

    def load_predict_dataset(self) -> Optional[pd.DataFrame]:
        """예측용 데이터셋 로드"""
        key = "ml_dataset/predict/latest.parquet"

        try:
            obj = self.s3_client.get_object(key)
            print(f"📂 예측 데이터셋 로드: {key}")
            return pd.read_parquet(io.BytesIO(obj))
        except Exception as e:
            print(f"❌ 예측 데이터셋 로드 실패: {e}")
            return None

    def save_csv_to_s3(self, df: pd.DataFrame, key: str) -> str:
        """DataFrame을 CSV로 S3에 저장 (마스터 데이터용)"""
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8')
        csv_content = csv_buffer.getvalue()

        self.s3_client.put_object(key, csv_content, content_type="text/csv")
        print(f"마스터 CSV 저장: s3://{self.s3_client.bucket_name}/{key}")
        return key

    def load_csv_from_s3(self, key: str) -> pd.DataFrame:
        """S3에서 CSV를 로드하여 DataFrame으로 변환"""
        csv_content = self.s3_client.get_object(key)
        return pd.read_csv(io.StringIO(csv_content.decode('utf-8')))

    def get_data_inventory(self) -> Dict[str, int]:
        """S3 데이터 인벤토리 조회"""
        inventory = {
            "raw_data": len(self.s3_client.list_objects(prefix="raw/")),
            "processed_data": len(self.s3_client.list_objects(prefix="processed/")),
            "train_datasets": len(self.s3_client.list_objects(prefix="ml_dataset/train/")),
            "predict_datasets": len(self.s3_client.list_objects(prefix="ml_dataset/predict/")),
            "master_data": len([k for k in self.s3_client.list_objects() if k.endswith('.csv')]),
            "total": len(self.s3_client.list_objects())
        }
        return inventory
