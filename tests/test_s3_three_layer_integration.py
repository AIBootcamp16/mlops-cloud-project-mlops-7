"""
S3 3-Layer Data Integration Test (Raw → Processed → ML Dataset)

This test validates that mock weather data is properly stored across all three data layers:
1. Raw layer: Original API response data
2. Processed layer: Parsed and structured data
3. ML Dataset layer: Feature-engineered data ready for ML
"""

import sys
import os
from datetime import datetime, timezone

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.data.weather_processor import WeatherDataProcessor
from src.utils.config import KMAApiConfig, S3Config
from src.storage.s3_client import S3StorageClient, WeatherDataS3Handler


def create_mock_asos_data():
    """Generate mock ASOS data with all weather fields"""
    return """<?xml version="1.0" encoding="UTF-8"?>
<response>
    <header>
        <resultCode>00</resultCode>
        <resultMsg>NORMAL_SERVICE</resultMsg>
    </header>
    <body>
        <items>
            <item>
                <stnId>108</stnId>
                <tm>202509301400</tm>
                <ta>22.5</ta>
                <ws>2.3</ws>
                <hm>65</hm>
                <pa>1013.2</pa>
                <rn>0</rn>
                <wd>270</wd>
                <td>15.2</td>
                <ca>3</ca>
                <vs>15000</vs>
                <ss>8.5</ss>
            </item>
            <item>
                <stnId>112</stnId>
                <tm>202509301400</tm>
                <ta>23.1</ta>
                <ws>1.8</ws>
                <hm>58</hm>
                <pa>1014.5</pa>
                <rn>0</rn>
                <wd>180</wd>
                <td>14.8</td>
                <ca>2</ca>
                <vs>20000</vs>
                <ss>9.2</ss>
            </item>
            <item>
                <stnId>119</stnId>
                <tm>202509301400</tm>
                <ta>21.8</ta>
                <ws>3.1</ws>
                <hm>72</hm>
                <pa>1012.8</pa>
                <rn>0</rn>
                <wd>90</wd>
                <td>16.5</td>
                <ca>5</ca>
                <vs>12000</vs>
                <ss>7.8</ss>
            </item>
        </items>
    </body>
</response>"""


def create_mock_pm10_data():
    """Generate mock PM10 (air quality) data"""
    return """<?xml version="1.0" encoding="UTF-8"?>
<response>
    <header>
        <resultCode>00</resultCode>
        <resultMsg>NORMAL_SERVICE</resultMsg>
    </header>
    <body>
        <items>
            <item>
                <stnId>108</stnId>
                <msrDt>202509301400</msrDt>
                <msrVal>45</msrVal>
            </item>
            <item>
                <stnId>112</stnId>
                <msrDt>202509301400</msrDt>
                <msrVal>38</msrVal>
            </item>
            <item>
                <stnId>119</stnId>
                <msrDt>202509301400</msrDt>
                <msrVal>52</msrVal>
            </item>
        </items>
    </body>
</response>"""


def test_three_layer_data_flow():
    """Test complete data flow from raw to processed to ML dataset"""

    print("="*80)
    print("S3 3-Layer Data Integration Test")
    print("="*80)

    # Initialize configurations
    kma_config = KMAApiConfig.from_env()
    s3_config = S3Config.from_env()

    # Initialize S3 client and handler
    s3_client = S3StorageClient(
        bucket_name=s3_config.bucket_name,
        aws_access_key_id=s3_config.aws_access_key_id,
        aws_secret_access_key=s3_config.aws_secret_access_key,
        region_name=s3_config.region_name,
        endpoint_url=s3_config.endpoint_url
    )
    weather_handler = WeatherDataS3Handler(s3_client)

    # Initialize weather processor
    processor = WeatherDataProcessor(kma_config, s3_config)

    # Step 1: Get inventory before test
    print("\n[STEP 1] S3 Inventory Before Test")
    print("-" * 80)
    inventory_before = weather_handler.get_data_inventory()
    print(f"Raw data files:       {inventory_before['raw_data']}")
    print(f"Processed data files: {inventory_before['processed_data']}")
    print(f"ML datasets:          {inventory_before['ml_datasets']}")
    print(f"Total files:          {inventory_before['total']}")

    # Step 2: Generate mock data
    print("\n[STEP 2] Generating Mock Weather Data")
    print("-" * 80)
    mock_asos = create_mock_asos_data()
    mock_pm10 = create_mock_pm10_data()
    print(f"✓ Mock ASOS data generated ({len(mock_asos)} bytes)")
    print(f"✓ Mock PM10 data generated ({len(mock_pm10)} bytes)")

    # Step 3: Process and store data (raw → processed → ml_dataset)
    print("\n[STEP 3] Processing and Storing Data Across All Layers")
    print("-" * 80)
    timestamp = datetime.now(tz=timezone.utc)

    stored_keys = processor.process_and_store_weather_data(
        asos_raw=mock_asos,
        pm10_raw=mock_pm10,
        timestamp=timestamp
    )

    if stored_keys:
        print(f"✓ Total {len(stored_keys)} objects stored successfully")
        for key_type, s3_key in stored_keys.items():
            print(f"  - {key_type}: {s3_key}")
    else:
        print("✗ No data was stored")
        return False

    # Step 4: Verify data in each layer
    print("\n[STEP 4] Verifying Data in Each Layer")
    print("-" * 80)

    # Layer 1: Raw data
    raw_asos_key = stored_keys.get('asos_raw')
    raw_pm10_key = stored_keys.get('pm10_raw')

    if raw_asos_key:
        raw_asos_content = s3_client.get_object(raw_asos_key)
        print(f"✓ Layer 1 (Raw ASOS): {len(raw_asos_content)} bytes")
        print(f"  Path: s3://{s3_client.bucket_name}/{raw_asos_key}")

    if raw_pm10_key:
        raw_pm10_content = s3_client.get_object(raw_pm10_key)
        print(f"✓ Layer 1 (Raw PM10): {len(raw_pm10_content)} bytes")
        print(f"  Path: s3://{s3_client.bucket_name}/{raw_pm10_key}")

    # Layer 2: Processed data
    processed_asos_key = stored_keys.get('asos_parsed')
    processed_pm10_key = stored_keys.get('pm10_parsed')

    if processed_asos_key:
        import json
        processed_asos = json.loads(s3_client.get_object(processed_asos_key))
        print(f"✓ Layer 2 (Processed ASOS): {len(processed_asos)} records")
        print(f"  Path: s3://{s3_client.bucket_name}/{processed_asos_key}")
        print(f"  Sample: {processed_asos[0] if processed_asos else 'N/A'}")

    if processed_pm10_key:
        processed_pm10 = json.loads(s3_client.get_object(processed_pm10_key))
        print(f"✓ Layer 2 (Processed PM10): {len(processed_pm10)} records")
        print(f"  Path: s3://{s3_client.bucket_name}/{processed_pm10_key}")
        print(f"  Sample: {processed_pm10[0] if processed_pm10 else 'N/A'}")

    # Layer 3: ML Dataset
    ml_dataset_key = stored_keys.get('ml_dataset')

    if ml_dataset_key:
        import io
        import pandas as pd
        ml_content = s3_client.get_object(ml_dataset_key)
        ml_df = pd.read_parquet(io.BytesIO(ml_content))
        print(f"✓ Layer 3 (ML Dataset): {len(ml_df)} rows, {len(ml_df.columns)} columns")
        print(f"  Path: s3://{s3_client.bucket_name}/{ml_dataset_key}")
        print(f"  Columns: {list(ml_df.columns[:10])}...")  # Show first 10 columns
        print(f"  Sample row:")
        if not ml_df.empty:
            sample = ml_df.iloc[0].to_dict()
            for key, value in list(sample.items())[:5]:  # Show first 5 fields
                print(f"    {key}: {value}")

    # Step 5: Get inventory after test
    print("\n[STEP 5] S3 Inventory After Test")
    print("-" * 80)
    inventory_after = weather_handler.get_data_inventory()
    print(f"Raw data files:       {inventory_after['raw_data']} (+{inventory_after['raw_data'] - inventory_before['raw_data']})")
    print(f"Processed data files: {inventory_after['processed_data']} (+{inventory_after['processed_data'] - inventory_before['processed_data']})")
    print(f"ML datasets:          {inventory_after['ml_datasets']} (+{inventory_after['ml_datasets'] - inventory_before['ml_datasets']})")
    print(f"Total files:          {inventory_after['total']} (+{inventory_after['total'] - inventory_before['total']})")

    # Step 6: Validation
    print("\n[STEP 6] Validation Summary")
    print("-" * 80)

    validation_results = {
        'Raw ASOS stored': raw_asos_key is not None,
        'Raw PM10 stored': raw_pm10_key is not None,
        'Processed ASOS stored': processed_asos_key is not None,
        'Processed PM10 stored': processed_pm10_key is not None,
        'ML Dataset stored': ml_dataset_key is not None,
    }

    all_passed = all(validation_results.values())

    for check, passed in validation_results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {check}")

    print("\n" + "="*80)
    if all_passed:
        print("✓ ALL TESTS PASSED - Data successfully stored in all 3 layers!")
        print("  → Raw layer: Original API responses")
        print("  → Processed layer: Parsed and structured data")
        print("  → ML Dataset layer: Feature-engineered data ready for training")
    else:
        print("✗ SOME TESTS FAILED - Please check the logs above")
    print("="*80)

    return all_passed


if __name__ == "__main__":
    try:
        success = test_three_layer_data_flow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)