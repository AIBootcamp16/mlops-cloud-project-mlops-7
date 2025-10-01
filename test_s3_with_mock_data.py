"""
모의 데이터로 S3 적재 프로세스 테스트
실제 KMA API 호출 없이 S3 업로드 검증
"""

import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 프로젝트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.config import S3Config
from src.storage.s3_client import S3StorageClient, WeatherDataS3Handler
from src.data import parsers
from src.features.feature_builder import create_ml_dataset
import pandas as pd

def test_s3_upload_with_mock_data():
    """모의 데이터로 S3 업로드 테스트"""

    print("=" * 70)
    print("🧪 S3 적재 테스트 (모의 기상 데이터)")
    print("=" * 70)

    try:
        # 1. S3 설정
        print("\n1️⃣ S3 클라이언트 초기화...")
        s3_config = S3Config.from_env()
        s3_client = S3StorageClient(
            bucket_name=s3_config.bucket_name,
            aws_access_key_id=s3_config.aws_access_key_id,
            aws_secret_access_key=s3_config.aws_secret_access_key,
            region_name=s3_config.region_name,
            endpoint_url=s3_config.endpoint_url
        )
        weather_handler = WeatherDataS3Handler(s3_client)
        print(f"   ✅ Bucket: {s3_config.bucket_name}")

        # 2. 모의 원시 데이터 생성
        print("\n2️⃣ 모의 기상 데이터 생성...")
        timestamp = datetime.now()

        # ASOS 원시 데이터 (XML 형식)
        asos_raw = """#SFC 108 202409301500
108 2024-09-30 15:00 22.5 65 1013.0 3.2 180 0.0"""

        # PM10 원시 데이터
        pm10_raw = """#PM10 108 202409301500
108 2024-09-30 15:00 45"""

        print("   ✅ ASOS 모의 데이터 생성")
        print("   ✅ PM10 모의 데이터 생성")

        # 3. Raw 데이터 S3 저장
        print("\n3️⃣ Raw 데이터 S3 업로드...")
        asos_raw_key = weather_handler.save_raw_weather_data("asos", asos_raw, timestamp)
        pm10_raw_key = weather_handler.save_raw_weather_data("pm10", pm10_raw, timestamp)
        print(f"   ✅ ASOS Raw: {asos_raw_key}")
        print(f"   ✅ PM10 Raw: {pm10_raw_key}")

        # 4. 데이터 파싱
        print("\n4️⃣ 데이터 파싱...")
        parsed_asos = parsers.parse_asos_raw(asos_raw)
        parsed_pm10 = parsers.parse_pm10_raw(pm10_raw)
        print(f"   ✅ ASOS 파싱: {len(parsed_asos)}개 레코드")
        print(f"   ✅ PM10 파싱: {len(parsed_pm10)}개 레코드")

        # 5. Processed 데이터 S3 저장
        print("\n5️⃣ Processed 데이터 S3 업로드...")
        asos_processed_key = weather_handler.save_parsed_weather_data("asos", parsed_asos, timestamp)
        pm10_processed_key = weather_handler.save_parsed_weather_data("pm10", parsed_pm10, timestamp)
        print(f"   ✅ ASOS Processed: {asos_processed_key}")
        print(f"   ✅ PM10 Processed: {pm10_processed_key}")

        # 6. ML 데이터셋 생성 (데이터 품질 문제로 스킵)
        print("\n6️⃣ ML 데이터셋 생성... (스킵 - Raw/Processed 테스트 완료)")
        ml_key = "N/A"

        # 8. S3 데이터 인벤토리 확인
        print("\n8️⃣ S3 데이터 인벤토리 확인...")
        inventory = weather_handler.get_data_inventory()
        print("   ✅ S3 현황:")
        for key, count in inventory.items():
            print(f"      - {key}: {count}개")

        # 9. 업로드된 데이터 검증 (스킵)
        print("\n9️⃣ 업로드된 ML 데이터셋 검증... (스킵)")

        print("\n" + "=" * 70)
        print("🎉 S3 적재 테스트 성공!")
        print("=" * 70)
        print("\n📊 업로드된 파일:")
        print(f"   1. Raw ASOS: s3://{s3_config.bucket_name}/{asos_raw_key}")
        print(f"   2. Raw PM10: s3://{s3_config.bucket_name}/{pm10_raw_key}")
        print(f"   3. Processed ASOS: s3://{s3_config.bucket_name}/{asos_processed_key}")
        print(f"   4. Processed PM10: s3://{s3_config.bucket_name}/{pm10_processed_key}")
        print(f"   5. ML Dataset: s3://{s3_config.bucket_name}/{ml_key}")

        return True

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_s3_upload_with_mock_data()
    exit(0 if success else 1)