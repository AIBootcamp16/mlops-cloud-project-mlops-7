"""
Airflow DAG for weekly master training dataset Rolling Window cleanup.

This DAG runs weekly to:
1. Apply Rolling Window (21 months = 630 days) to master CSV
2. Remove old data, duplicates, and sort records
3. Validate cleanup completion

Note: Hourly data is accumulated by weather_data_pipeline DAG.
This DAG only performs cleanup.

Schedule: Every Sunday at 2 AM (weekly)
Author: MLOps Team
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
import sys
import os

# Add project source to Python path
sys.path.append('/opt/airflow/dags')
sys.path.append('/opt/airflow/src')
sys.path.append('/opt/airflow')

# Default arguments for all tasks
default_args = {
    'owner': 'mlops-team',
    'depends_on_past': False,
    'start_date': datetime(2025, 10, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
    'catchup': False
}

# DAG definition
dag = DAG(
    'master_data_rolling_window_weekly',
    default_args=default_args,
    description='Weekly Rolling Window cleanup for master training dataset (21 months)',
    schedule_interval='0 2 * * 0',  # Every Sunday at 2 AM
    max_active_runs=1,
    tags=['master-data', 'rolling-window', 'cleanup', 'weekly']
)

def apply_rolling_window(**context):
    """
    Apply Rolling Window (21 months = 630 days) to master CSV.
    Removes old data, duplicates, and sorts records.
    """
    from src.utils.config import S3Config
    from src.storage.s3_client import S3StorageClient, WeatherDataS3Handler
    from datetime import datetime, timedelta
    import pandas as pd

    print("=== Applying Rolling Window to master CSV ===")

    # Initialize S3 handler
    s3_config = S3Config.from_env()
    s3_client = S3StorageClient(
        bucket_name=s3_config.bucket_name,
        aws_access_key_id=s3_config.aws_access_key_id,
        aws_secret_access_key=s3_config.aws_secret_access_key,
        region_name=s3_config.region_name,
        endpoint_url=s3_config.endpoint_url
    )
    weather_handler = WeatherDataS3Handler(s3_client)

    # Load existing master CSV
    master_key = "weather_pm10_integrated_full.csv"
    try:
        existing_df = weather_handler.load_csv_from_s3(master_key)
        print(f"📂 Loaded master CSV: {len(existing_df)} records")
    except Exception as e:
        print(f"❌ Failed to load master CSV: {e}")
        raise Exception(f"Master CSV not found: {e}")

    records_before = len(existing_df)

    # Convert datetime column
    if 'datetime' in existing_df.columns:
        existing_df['datetime'] = pd.to_datetime(existing_df['datetime'])

        # Apply Rolling Window (21 months = 630 days)
        retention_days = 630
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        cleaned_df = existing_df[existing_df['datetime'] >= cutoff_date]

        records_after_cutoff = len(cleaned_df)
        removed_by_cutoff = records_before - records_after_cutoff

        print(f"🔄 Rolling Window (630 days) applied:")
        print(f"   - Cutoff date: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   - Records before: {records_before:,}")
        print(f"   - Records after cutoff: {records_after_cutoff:,}")
        print(f"   - Removed by cutoff: {removed_by_cutoff:,}")

        # Remove duplicates (keep latest)
        duplicate_columns = ['datetime', 'STN']
        cleaned_df = cleaned_df.drop_duplicates(subset=duplicate_columns, keep='last')

        records_after_dedup = len(cleaned_df)
        removed_by_dedup = records_after_cutoff - records_after_dedup

        print(f"🧹 Duplicates removed:")
        print(f"   - Records after dedup: {records_after_dedup:,}")
        print(f"   - Removed by dedup: {removed_by_dedup:,}")

        # Sort by datetime and station
        cleaned_df = cleaned_df.sort_values(duplicate_columns)
        cleaned_df = cleaned_df.reset_index(drop=True)

    else:
        print("⚠️ Warning: 'datetime' column not found, skipping cleanup")
        cleaned_df = existing_df

    # Save cleaned master CSV
    weather_handler.save_csv_to_s3(cleaned_df, master_key)

    records_final = len(cleaned_df)
    total_removed = records_before - records_final

    print(f"✅ Rolling Window cleanup completed:")
    print(f"   - Final records: {records_final:,}")
    print(f"   - Total removed: {total_removed:,}")
    print(f"   - Retention period: {retention_days} days (21 months)")

    result = {
        'status': 'success',
        'records_before': records_before,
        'records_after': records_final,
        'records_removed': total_removed,
        'removed_by_cutoff': removed_by_cutoff,
        'removed_by_dedup': removed_by_dedup,
        'retention_cutoff': cutoff_date.strftime('%Y-%m-%d %H:%M:%S'),
        'csv_key': master_key
    }

    return result

def validate_cleanup(**context):
    """
    Validate that Rolling Window cleanup completed successfully.
    """
    from src.utils.config import S3Config
    from src.storage.s3_client import S3StorageClient, WeatherDataS3Handler
    import pandas as pd

    print("=== Validating Rolling Window cleanup ===")

    # Get cleanup result from previous task
    ti = context['ti']
    cleanup_result = ti.xcom_pull(task_ids='apply_rolling_window')

    if not cleanup_result or cleanup_result.get('status') != 'success':
        raise ValueError("Rolling Window cleanup validation failed")

    # Initialize S3 handler
    s3_config = S3Config.from_env()
    s3_client = S3StorageClient(
        bucket_name=s3_config.bucket_name,
        aws_access_key_id=s3_config.aws_access_key_id,
        aws_secret_access_key=s3_config.aws_secret_access_key,
        region_name=s3_config.region_name,
        endpoint_url=s3_config.endpoint_url
    )
    weather_handler = WeatherDataS3Handler(s3_client)

    # Verify master CSV exists and can be loaded
    try:
        master_df = weather_handler.load_csv_from_s3("weather_pm10_integrated_full.csv")
        print(f"✅ Master CSV verified: {len(master_df):,} records, {len(master_df.columns)} columns")

        # Verify datetime range
        if 'datetime' in master_df.columns:
            master_df['datetime'] = pd.to_datetime(master_df['datetime'])
            date_min = master_df['datetime'].min()
            date_max = master_df['datetime'].max()
            print(f"📅 Date range: {date_min.strftime('%Y-%m-%d')} to {date_max.strftime('%Y-%m-%d')}")

            # Check for duplicates
            duplicate_count = master_df.duplicated(subset=['datetime', 'STN']).sum()
            if duplicate_count > 0:
                print(f"⚠️ Warning: Found {duplicate_count} duplicates (should be 0)")
            else:
                print(f"✅ No duplicates found")

    except Exception as e:
        raise ValueError(f"Failed to load master CSV: {e}")

    print("🎉 Rolling Window cleanup completed successfully!")
    print(f"📊 Final stats:")
    print(f"   - Records retained: {cleanup_result.get('records_after', 0):,}")
    print(f"   - Records removed: {cleanup_result.get('records_removed', 0):,}")
    print(f"   - Retention cutoff: {cleanup_result.get('retention_cutoff')}")

    return True

# Task definitions
start_task = DummyOperator(
    task_id='start_rolling_window_cleanup',
    dag=dag
)

apply_window_task = PythonOperator(
    task_id='apply_rolling_window',
    python_callable=apply_rolling_window,
    dag=dag
)

validate_task = PythonOperator(
    task_id='validate_cleanup',
    python_callable=validate_cleanup,
    dag=dag
)

end_task = DummyOperator(
    task_id='end_rolling_window_cleanup',
    dag=dag
)

# Task dependencies
start_task >> apply_window_task >> validate_task >> end_task
