import os
import sys
import pymysql
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

def get_mysql_connection():
    """MySQL 연결"""
    return pymysql.connect(
        host=os.getenv('MYSQL_HOST', 'mysql'),
        port=int(os.getenv('MYSQL_PORT', 3306)),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_ROOT_PASSWORD', 'mlops2025'),
        database=os.getenv('MYSQL_DATABASE', 'weather_mlops'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def insert_test_data():
    """테스트 데이터 생성 및 삽입 (다양한 쾌적 지수)"""
    
    # KST 시간대 설정
    kst = pytz.timezone('Asia/Seoul')
    current_time = datetime.now(kst)
    
    # 현재 시간을 정각으로 맞춤
    base_time = current_time.replace(minute=0, second=0, microsecond=0)
    
    # 다양한 쾌적 지수를 가진 테스트 데이터 생성 (현재 시간부터 24시간)
    test_data_list = []
    
    # 다양한 쾌적 지수 패턴 (24개)
    comfort_scores = [
        85.5, 92.3, 78.9, 65.4, 72.1, 88.7, 55.2, 48.6,
        95.1, 81.3, 68.9, 75.4, 42.1, 58.7, 89.2, 76.8,
        63.5, 52.8, 91.2, 84.6, 69.3, 57.9, 80.4, 73.2
    ]
    
    for i in range(24):
        prediction_time = base_time + timedelta(hours=i)
        comfort_score = comfort_scores[i]
        
        # 쾌적 지수에 따라 날씨 데이터 생성
        if comfort_score >= 80:  # 완벽한 날씨
            temperature = 22.0 + (i % 5)
            humidity = 50.0 + (i % 10)
            rainfall = 0.0
            pm10 = 15.0 + (i % 10)
            wind_speed = 2.0 + (i % 3) * 0.5
            pressure = 1013.0 + (i % 5)
        elif comfort_score >= 60:  # 쾌적한 날씨
            temperature = 18.0 + (i % 8)
            humidity = 60.0 + (i % 15)
            rainfall = 0.5 if i % 5 == 0 else 0.0
            pm10 = 30.0 + (i % 20)
            wind_speed = 3.0 + (i % 4) * 0.5
            pressure = 1010.0 + (i % 7)
        elif comfort_score >= 40:  # 보통 날씨
            temperature = 15.0 + (i % 12)
            humidity = 70.0 + (i % 20)
            rainfall = 1.5 if i % 3 == 0 else 0.0
            pm10 = 50.0 + (i % 30)
            wind_speed = 4.0 + (i % 5) * 0.5
            pressure = 1008.0 + (i % 8)
        else:  # 좋지 않은 날씨
            temperature = 10.0 + (i % 15)
            humidity = 80.0 + (i % 15)
            rainfall = 5.0 + (i % 10)
            pm10 = 80.0 + (i % 50)
            wind_speed = 6.0 + (i % 6) * 0.5
            pressure = 1005.0 + (i % 10)
        
        test_data = {
            'comfort_score': comfort_score,
            'temperature': temperature,
            'humidity': humidity,
            'rainfall': rainfall,
            'pm10': pm10,
            'wind_speed': wind_speed,
            'pressure': pressure,
            'prediction_datetime': prediction_time,
            'region': '서울',
            'station_id': '108',
            'model_name': 'test-model-v1'
        }
        
        test_data_list.append(test_data)
    
    # MySQL에 데이터 삽입
    conn = get_mysql_connection()
    inserted_count = 0
    
    try:
        with conn.cursor() as cursor:
            for data in test_data_list:
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
                        pressure = VALUES(pressure),
                        created_at = CURRENT_TIMESTAMP
                """
                cursor.execute(sql, (
                    data['comfort_score'],
                    data['temperature'],
                    data['humidity'],
                    data['rainfall'],
                    data['pm10'],
                    data['wind_speed'],
                    data['pressure'],
                    data['prediction_datetime'],
                    data['region'],
                    data['station_id'],
                    data['model_name']
                ))
                inserted_count += 1
                print(f"✅ [{data['prediction_datetime'].strftime('%Y-%m-%d %H:%M')}] 쾌적지수: {data['comfort_score']:.1f} 삽입 완료")
        
        conn.commit()
        print(f"\n🎉 총 {inserted_count}개의 테스트 데이터가 MySQL에 삽입되었습니다!")
        print(f"📊 쾌적 지수 범위: {min(comfort_scores):.1f} ~ {max(comfort_scores):.1f}")
        print(f"⏰ 데이터 시간 범위: {base_time.strftime('%Y-%m-%d %H:%M')} ~ {(base_time + timedelta(hours=23)).strftime('%Y-%m-%d %H:%M')}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 데이터 삽입 중 오류 발생: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 프론트엔드 테스트용 MySQL 데이터 삽입 시작")
    print("=" * 60)
    insert_test_data()
    print("=" * 60) 