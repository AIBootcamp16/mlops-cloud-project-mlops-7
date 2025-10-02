import sys
sys.path.append('/app')

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pandas as pd


def fetch_task(**context):
    """Task 1: S3에서 최신 parquet 데이터 로드"""
    from batch.jobs.fetch import get_latest_parquet_from_s3
    
    print("S3에서 최신 데이터 로드 중...")
    df = get_latest_parquet_from_s3()
    
    context['task_instance'].xcom_push(key='raw_data', value=df.to_json())
    print(f"데이터 로드 완료: {len(df)} 건")


def inference_task(**context):
    """Task 2: 모델 추론"""
    from batch.jobs.infer import batch_predict
    
    raw_data_json = context['task_instance'].xcom_pull(
        task_ids='fetch_data', 
        key='raw_data'
    )
    df = pd.read_json(raw_data_json)
    
    print("배치 추론 시작...")
    result_df = batch_predict(df)
    
    context['task_instance'].xcom_push(key='predictions', value=result_df.to_json())
    print(f"추론 완료: {len(result_df)} 건")


def upsert_task(**context):
    """Task 3: MySQL에 저장"""
    from batch.jobs.upsert import upsert_predictions
    
    predictions_json = context['task_instance'].xcom_pull(
        task_ids='inference', 
        key='predictions'
    )
    result_df = pd.read_json(predictions_json)
    
    print("DB 저장 중...")
    upsert_predictions(result_df)
    print(f"DB 저장 완료: {len(result_df)} 건")


default_args = {
    'owner': 'mlops-team',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'batch_inference_pipeline',
    default_args=default_args,
    description='날씨 comfort score 배치 추론',
    schedule_interval='15 * * * *',  # 매시간 15분에 실행
    catchup=False,
    tags=['inference', 'weather', 'batch'],
) as dag:
    
    fetch = PythonOperator(
        task_id='fetch_data',
        python_callable=fetch_task,
    )
    
    infer = PythonOperator(
        task_id='inference',
        python_callable=inference_task,
    )
    
    upsert = PythonOperator(
        task_id='upsert_to_db',
        python_callable=upsert_task,
    )
    
    fetch >> infer >> upsert