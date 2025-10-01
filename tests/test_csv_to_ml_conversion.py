"""
기존 CSV(49개 필드)를 ML 데이터셋(34개 컬럼)으로 변환 테스트
"""

import sys
import os
import pandas as pd

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.data.weather_processor import WeatherDataProcessor
from src.utils.config import KMAApiConfig, S3Config


def test_csv_to_ml_conversion():
    """기존 CSV를 34개 컬럼 ML 데이터셋으로 변환 테스트"""

    print("="*80)
    print("CSV → ML 데이터셋 변환 테스트")
    print("="*80)

    # 1. 기존 CSV 로드
    csv_path = 'weather_pm10_integrated_full.csv'
    if not os.path.exists(csv_path):
        print(f"❌ 파일 없음: {csv_path}")
        return False

    print(f"\n[STEP 1] 기존 CSV 로드")
    print("-"*80)
    df = pd.read_csv(csv_path, low_memory=False)
    print(f"✓ 원본 데이터: {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"✓ 샘플 데이터 (첫 5개 행)")

    # 2. WeatherDataProcessor 초기화
    print(f"\n[STEP 2] WeatherDataProcessor 초기화")
    print("-"*80)
    kma_config = KMAApiConfig.from_env()
    s3_config = S3Config.from_env()
    processor = WeatherDataProcessor(kma_config, s3_config)
    print(f"✓ Processor 초기화 완료")

    # 3. 샘플 데이터로 변환 테스트 (처음 100개 행)
    print(f"\n[STEP 3] 변환 테스트 (샘플 100개 행)")
    print("-"*80)
    sample_df = df.head(100).copy()

    # 변환 실행
    raw_data_for_ml = processor._convert_csv_to_feature_format(sample_df)

    print(f"✓ ASOS 레코드: {len(raw_data_for_ml['asos'])}개")
    print(f"✓ PM10 레코드: {len(raw_data_for_ml['pm10'])}개")

    if raw_data_for_ml['asos']:
        print(f"\n샘플 ASOS 레코드:")
        sample_asos = raw_data_for_ml['asos'][0]
        for key, value in sample_asos.items():
            print(f"  {key}: {value}")

    # 4. ML 데이터셋 생성
    print(f"\n[STEP 4] ML 데이터셋 생성")
    print("-"*80)
    from src.features.feature_builder import create_ml_dataset

    ml_dataset = create_ml_dataset(raw_data_for_ml, include_labels=True)

    if ml_dataset.empty:
        print("❌ ML 데이터셋 생성 실패")
        return False

    print(f"✓ ML 데이터셋: {ml_dataset.shape[0]} rows × {ml_dataset.shape[1]} columns")
    print(f"\n컬럼 목록 ({len(ml_dataset.columns)}개):")
    for i, col in enumerate(ml_dataset.columns, 1):
        print(f"  {i:2d}. {col}")

    # 5. 검증
    print(f"\n[STEP 5] 검증")
    print("-"*80)

    expected_columns = 34
    actual_columns = len(ml_dataset.columns)

    # 필수 컬럼 확인
    required_fields = [
        'temperature', 'wind_speed', 'humidity', 'pressure',
        'rainfall', 'wind_direction', 'dew_point', 'cloud_amount',
        'visibility', 'sunshine', 'pm10', 'comfort_score'
    ]

    missing_fields = [f for f in required_fields if f not in ml_dataset.columns]

    print(f"기대 컬럼 수: {expected_columns}")
    print(f"실제 컬럼 수: {actual_columns}")

    if missing_fields:
        print(f"❌ 누락된 필드: {missing_fields}")
        return False
    else:
        print(f"✓ 모든 필수 필드 포함")

    if actual_columns == expected_columns:
        print(f"✅ 변환 성공: 34개 컬럼 생성 완료")

        # 샘플 데이터 출력
        print(f"\n샘플 데이터 (첫 번째 행):")
        sample_row = ml_dataset.iloc[0].to_dict()
        for key, value in list(sample_row.items())[:10]:
            print(f"  {key}: {value}")

        return True
    else:
        print(f"❌ 컬럼 수 불일치: {actual_columns} != {expected_columns}")
        return False


if __name__ == "__main__":
    try:
        success = test_csv_to_ml_conversion()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)