import os
import pymysql
from datetime import datetime
import pandas as pd

def get_mysql_connection():
    """MySQL 연결"""
    return pymysql.connect(
        host=os.getenv('MYSQL_HOST', 'mysql'),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_ROOT_PASSWORD'),
        database=os.getenv('MYSQL_DATABASE', 'weather_mlops'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def query_prediction_by_datetime(prediction_datetime: datetime, station_id: str = '108'):
    """특정 시간대 예측 결과 조회"""
    conn = get_mysql_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT * FROM weather_predictions 
                WHERE prediction_datetime = %s AND station_id = %s
            """
            cursor.execute(sql, (prediction_datetime, station_id))
            return cursor.fetchone()
    finally:
        conn.close()

def save_prediction_to_mysql(result_df: pd.DataFrame, prediction_datetime: datetime, model_name: str = 'weather-predictor-018'):
    """예측 결과를 MySQL에 저장 (UPSERT)"""
    conn = get_mysql_connection()
    try:
        with conn.cursor() as cursor:
            for _, row in result_df.iterrows():
                sql = """
                    INSERT INTO weather_predictions 
                    (comfort_score, temperature, humidity, rainfall, pm10, 
                     wind_speed, pressure, prediction_datetime, region, station_id, model_name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        comfort_score = VALUES(comfort_score),
                        temperature = VALUES(temperature),
                        humidity = VALUES(humidity),
                        created_at = CURRENT_TIMESTAMP
                """
                cursor.execute(sql, (
                    row.get('predicted_comfort_score'),
                    row.get('temperature'),
                    row.get('humidity'),
                    row.get('rainfall'),
                    row.get('pm10'),
                    row.get('wind_speed'),
                    row.get('pressure'),
                    prediction_datetime,
                    row.get('region'),
                    row.get('station_id', '108'),
                    model_name
                ))
        conn.commit()
        print(f"✅ MySQL 저장 완료: {prediction_datetime}")
    finally:
        conn.close() 