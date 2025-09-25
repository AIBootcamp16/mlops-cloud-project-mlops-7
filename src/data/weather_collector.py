import requests
import pandas as pd
import os
from datetime import datetime, timedelta
import time

def collect_weather_data():
    print("🌤️ 기상청 API 데이터 수집 시작...")
    
    # 기상청 API 설정 (실제 API 키 필요)
    api_key = os.getenv('WEATHER_API_KEY', 'YOUR_API_KEY_HERE')
    
    # 더미 데이터 생성 (실제 API 호출 대신)
    print("📡 기상청 API 호출 중... (더미 데이터)")
    
    # 실제 기상청 API 호출 코드 (주석 처리)
    """
    # 실제 기상청 API 호출 예시
    base_url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    
    params = {
        'serviceKey': api_key,
        'pageNo': 1,
        'numOfRows': 1000,
        'dataType': 'JSON',
        'base_date': datetime.now().strftime('%Y%m%d'),
        'base_time': '0800',
        'nx': 55,  # 서울 격자 X
        'ny': 127  # 서울 격자 Y
    }
    
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        print("✅ API 호출 성공!")
    else:
        print(f"❌ API 호출 실패: {response.status_code}")
        return None
    """
    
    # 더미 데이터 생성 (7일치)
    weather_data = []
    
    for i in range(168):  # 7일 * 24시간
        date_time = datetime.now() - timedelta(hours=168-i)
        
        # 랜덤하지만 현실적인 기상 데이터
        temp_base = 20 + 10 * (0.5 - abs((i % 24 - 12) / 24))  # 일교차
        
        weather_data.append({
            'datetime': date_time.strftime('%Y-%m-%d %H:%M:%S'),
            'temperature': round(temp_base + (i % 7) * 2 + (i % 3 - 1), 1),
            'humidity': round(50 + (i % 11) * 3 + (i % 5 - 2) * 2, 1),
            'pressure': round(1013 + (i % 13 - 6) * 0.5, 1),
            'wind_speed': round(abs((i % 7 - 3) * 1.2), 1),
            'location': 'Seoul'
        })
        
        # 진행상황 표시
        if i % 50 == 0:
            print(f"진행률: {i/168*100:.0f}%")
            time.sleep(0.1)  # API 호출 시뮬레이션
    
    # DataFrame 생성
    df = pd.DataFrame(weather_data)
    
    print(f"✅ 데이터 수집 완료: {len(df)}개 레코드")
    print(f"기간: {df['datetime'].min()} ~ {df['datetime'].max()}")
    print("\n📊 데이터 미리보기:")
    print(df.head())
    print(f"\n📈 통계 요약:")
    print(df.describe())
    
    # 데이터 저장
    os.makedirs('data/raw', exist_ok=True)
    df.to_csv('data/raw/weather_raw_data.csv', index=False)
    
    print(f"\n💾 원본 데이터 저장 완료: data/raw/weather_raw_data.csv")
    
    return df

def test_api_connection():
    """API 연결 테스트"""
    print("🔍 기상청 API 연결 테스트...")
    
    api_key = os.getenv('WEATHER_API_KEY')
    if not api_key or api_key == 'YOUR_API_KEY_HERE':
        print("❌ WEATHER_API_KEY 환경변수가 설정되지 않았습니다")
        print("💡 .env 파일에 WEATHER_API_KEY를 설정하세요")
        return False
    
    # 간단한 API 테스트 (실제로는 기상청 API 호출)
    print("✅ API 키 확인됨 (실제 연결 테스트는 구현 필요)")
    return True

if __name__ == "__main__":
    # API 연결 테스트
    test_api_connection()
    
    # 데이터 수집 실행
    collect_weather_data()
    
    print("\n🎉 데이터 수집 단계 완료!")
    print("다음 단계: python src/preprocessing/clean_data.py")