#!/usr/bin/env python3
"""FastAPI 서버 테스트 스크립트"""

import requests
import json
import time
from datetime import datetime

def test_api_server(base_url="http://localhost:8000"):
    """API 서버 테스트"""

    print("🚀 FastAPI 서버 테스트 시작")
    print(f"📍 Base URL: {base_url}")

    # 1. 루트 엔드포인트 테스트
    print("\n1. 루트 엔드포인트 테스트")
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ Status: {response.status_code}")
        print(f"📄 Response: {response.json()}")
    except Exception as e:
        print(f"❌ 루트 테스트 실패: {e}")
        return

    # 2. 헬스 체크 테스트
    print("\n2. 헬스 체크 테스트")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ Status: {response.status_code}")
        health_data = response.json()
        print(f"🏥 Health: {health_data}")
    except Exception as e:
        print(f"❌ 헬스 체크 실패: {e}")

    # 3. 관측소 목록 테스트
    print("\n3. 관측소 목록 테스트")
    try:
        response = requests.get(f"{base_url}/stations")
        print(f"✅ Status: {response.status_code}")
        stations_data = response.json()
        print(f"🏢 관측소 수: {stations_data['total_count']}개")
    except Exception as e:
        print(f"❌ 관측소 목록 테스트 실패: {e}")

    # 4. 모델 정보 테스트
    print("\n4. 모델 정보 테스트")
    try:
        response = requests.get(f"{base_url}/model/info")
        print(f"✅ Status: {response.status_code}")
        model_info = response.json()
        print(f"🤖 모델: {model_info['model_metadata']}")
    except Exception as e:
        print(f"❌ 모델 정보 테스트 실패: {e}")

    # 5. 예측 API 테스트 (기본 요청)
    print("\n5. 예측 API 테스트 (기본 요청)")
    try:
        request_data = {}
        response = requests.post(f"{base_url}/predict", json=request_data)
        print(f"✅ Status: {response.status_code}")
        if response.status_code == 200:
            predict_data = response.json()
            print(f"📊 예측 결과: {len(predict_data['predictions'])}개 관측소")
            print(f"⏱️ 처리 시간: {predict_data['processing_time']:.3f}초")
        else:
            print(f"❌ 예측 실패: {response.text}")
    except Exception as e:
        print(f"❌ 예측 테스트 실패: {e}")

    # 6. 예측 API 테스트 (상세 요청)
    print("\n6. 예측 API 테스트 (상세 요청)")
    try:
        request_data = {
            "station_ids": ["108", "112"],
            "datetime": datetime.now().isoformat() + "Z",
            "features": {
                "temperature": 23.5,
                "pm10": 15.0
            }
        }
        response = requests.post(f"{base_url}/predict", json=request_data)
        print(f"✅ Status: {response.status_code}")
        if response.status_code == 200:
            predict_data = response.json()
            print(f"📊 예측 결과: {len(predict_data['predictions'])}개 관측소")
            for pred in predict_data['predictions'][:2]:  # 처음 2개만 출력
                print(f"  🏢 {pred['station_id']}: 온도 {pred['predicted_temperature']:.1f}°C, PM10 {pred['predicted_pm10']:.1f}㎍/m³")
        else:
            print(f"❌ 예측 실패: {response.text}")
    except Exception as e:
        print(f"❌ 상세 예측 테스트 실패: {e}")

    print("\n🎉 API 테스트 완료!")

if __name__ == "__main__":
    test_api_server()