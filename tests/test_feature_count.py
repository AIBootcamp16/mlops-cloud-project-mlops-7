"""
테스트: ML 데이터셋의 피처 개수 확인
"""

import sys
import os
from datetime import datetime, timezone

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.features.feature_builder import create_ml_dataset


def test_feature_count():
    """30개 피처가 생성되는지 확인"""

    # 모의 데이터
    raw_data = {
        "asos": [
            {
                "station_id": "108",
                "observed_at": datetime(2025, 9, 30, 14, 0, 0, tzinfo=timezone.utc),
                "category": "asos",
                "value": 22.5,
                "unit": "°C"
            }
        ],
        "pm10": [
            {
                "station_id": "108",
                "observed_at": datetime(2025, 9, 30, 14, 0, 0, tzinfo=timezone.utc),
                "category": "pm10",
                "value": 45.0,
                "unit": "μg/m³"
            }
        ]
    }

    # ML 데이터셋 생성 (추론용 - label 없음)
    df_inference = create_ml_dataset(raw_data, include_labels=False)
    print(f"\n추론용 데이터셋 (include_labels=False):")
    print(f"  - 행 개수: {len(df_inference)}")
    print(f"  - 컬럼 개수: {len(df_inference.columns)}")
    print(f"  - 컬럼 목록:")
    for i, col in enumerate(df_inference.columns, 1):
        print(f"    {i:2d}. {col}")

    # ML 데이터셋 생성 (학습용 - label 포함)
    df_training = create_ml_dataset(raw_data, include_labels=True)
    print(f"\n학습용 데이터셋 (include_labels=True):")
    print(f"  - 행 개수: {len(df_training)}")
    print(f"  - 컬럼 개수: {len(df_training.columns)}")
    print(f"  - 컬럼 목록:")
    for i, col in enumerate(df_training.columns, 1):
        print(f"    {i:2d}. {col}")

    # 검증
    print(f"\n검증 결과:")
    print(f"  - 추론용 피처 개수: {len(df_inference.columns)} (목표: 30개)")
    print(f"  - 학습용 피처 개수: {len(df_training.columns)} (목표: 31개, 추론용 30개 + comfort_score 1개)")

    if len(df_inference.columns) < 30:
        print(f"  ❌ 부족한 피처 개수: {30 - len(df_inference.columns)}개")
        return False
    else:
        print(f"  ✅ 추론용 피처 30개 생성 완료")
        return True


if __name__ == "__main__":
    success = test_feature_count()
    sys.exit(0 if success else 1)