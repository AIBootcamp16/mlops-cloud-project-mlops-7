"""
S3 적재 실험 스크립트
간단한 테스트 데이터로 S3 업로드 프로세스를 검증합니다.
"""

import sys
import os
from datetime import datetime

# 프로젝트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.config import S3Config
from src.storage.s3_client import S3StorageClient, WeatherDataS3Handler
import pandas as pd

def test_s3_upload():
    """S3 업로드 테스트"""

    print("=" * 60)
    print("🧪 S3 적재 실험 시작")
    print("=" * 60)

    try:
        # 1. S3 설정 로드
        print("\n1️⃣ S3 설정 로드 중...")
        s3_config = S3Config.from_env()
        print(f"   ✅ Bucket: {s3_config.bucket_name}")
        print(f"   ✅ Region: {s3_config.region_name}")

        # 2. S3 클라이언트 초기화
        print("\n2️⃣ S3 클라이언트 초기화 중...")
        s3_client = S3StorageClient(
            bucket_name=s3_config.bucket_name,
            aws_access_key_id=s3_config.aws_access_key_id,
            aws_secret_access_key=s3_config.aws_secret_access_key,
            region_name=s3_config.region_name,
            endpoint_url=s3_config.endpoint_url
        )
        weather_handler = WeatherDataS3Handler(s3_client)
        print("   ✅ S3 클라이언트 초기화 완료")

        # 3. 테스트 데이터 생성
        print("\n3️⃣ 테스트 데이터 생성 중...")
        timestamp = datetime.now()

        # 원시 데이터 (Raw)
        test_raw_data = """<?xml version="1.0" encoding="UTF-8"?>
<response>
    <header><resultCode>00</resultCode></header>
    <body>
        <item>
            <stnId>108</stnId>
            <tm>2024-09-30 14:00</tm>
            <ta>22.5</ta>
        </item>
    </body>
</response>"""

        # 파싱된 데이터 (Processed)
        test_parsed_data = [
            {
                "station_id": "108",
                "observed_at": timestamp.isoformat(),
                "category": "asos",
                "value": 22.5,
                "unit": "°C"
            }
        ]

        # ML 데이터셋
        test_ml_dataset = pd.DataFrame([
            {
                "station_id": "108",
                "datetime": timestamp,
                "temperature": 22.5,
                "pm10": 45,
                "hour": 14,
                "is_rush_hour": False
            }
        ])

        print("   ✅ 테스트 데이터 생성 완료")

        # 4. Raw 데이터 업로드
        print("\n4️⃣ Raw 데이터 S3 업로드 중...")
        raw_key = weather_handler.save_raw_weather_data("asos", test_raw_data, timestamp)
        print(f"   ✅ Raw 데이터 업로드 완료: {raw_key}")

        # 5. Processed 데이터 업로드
        print("\n5️⃣ Processed 데이터 S3 업로드 중...")
        processed_key = weather_handler.save_parsed_weather_data("asos", test_parsed_data, timestamp)
        print(f"   ✅ Processed 데이터 업로드 완료: {processed_key}")

        # 6. ML 데이터셋 업로드
        print("\n6️⃣ ML 데이터셋 S3 업로드 중...")
        ml_key = weather_handler.save_ml_dataset(test_ml_dataset, timestamp)
        print(f"   ✅ ML 데이터셋 업로드 완료: {ml_key}")

        # 7. S3 데이터 인벤토리 확인
        print("\n7️⃣ S3 데이터 인벤토리 확인 중...")
        inventory = weather_handler.get_data_inventory()
        print("   ✅ S3 데이터 현황:")
        for key, count in inventory.items():
            print(f"      - {key}: {count}개")

        # 8. 업로드된 데이터 검증
        print("\n8️⃣ 업로드된 데이터 검증 중...")
        loaded_df = weather_handler.load_latest_ml_dataset()
        if loaded_df is not None and len(loaded_df) > 0:
            print(f"   ✅ 데이터 로드 성공: {len(loaded_df)}행, {len(loaded_df.columns)}열")
            print(f"   ✅ 컬럼: {list(loaded_df.columns)}")
        else:
            print("   ⚠️ 데이터 로드 실패")

        print("\n" + "=" * 60)
        print("🎉 S3 적재 실험 성공!")
        print("=" * 60)
        print("\n📊 업로드된 파일 경로:")
        print(f"   1. Raw: s3://{s3_config.bucket_name}/{raw_key}")
        print(f"   2. Processed: s3://{s3_config.bucket_name}/{processed_key}")
        print(f"   3. ML Dataset: s3://{s3_config.bucket_name}/{ml_key}")

        return True

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_s3_upload()
    exit(0 if success else 1)