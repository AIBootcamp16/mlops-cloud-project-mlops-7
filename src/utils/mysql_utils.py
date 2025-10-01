import os
import pymysql
from datetime import datetime
import pandas as pd


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