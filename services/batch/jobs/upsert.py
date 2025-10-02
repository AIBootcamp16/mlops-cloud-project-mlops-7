import os
import pandas as pd
from src.utils.mysql_utils import get_mysql_connection


def upsert_predictions(result_df: pd.DataFrame):
    """예측 결과를 MySQL에 저장 (UPSERT)"""
    print("💾 MySQL 저장 시작")
    
    conn = get_mysql_connection()
    
    try:
        with conn.cursor() as cursor:
            success_count = 0

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
                        rainfall = VALUES(rainfall),
                        pm10 = VALUES(pm10),
                        wind_speed = VALUES(wind_speed),
                        pressure = VALUES(pressure)
                """
                cursor.execute(sql, (
                    row.get('comfort_score'),
                    row.get('temperature'),
                    row.get('humidity'),
                    row.get('rainfall'),
                    row.get('pm10'),
                    row.get('wind_speed'),
                    row.get('pressure'),
                    row.get('datetime'),
                    row.get('region'),  
                    row.get('station_id', '108'),
                    row.get('model_version', os.getenv('CHAMPION_MODEL'))
                ))
                success_count += 1
                
        conn.commit()
        print(f"✅ MySQL 저장 완료: {success_count} 건")

    except Exception as e:
        conn.rollback()
        print(f"❌ MySQL 저장 실패: {str(e)}")
        raise

    finally:
        conn.close()