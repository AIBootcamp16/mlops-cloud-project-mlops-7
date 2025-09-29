import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="🌤️ 날씨 쾌적지수 예측",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API 엔드포인트 (Docker Compose 환경)
API_BASE_URL = "http://api-server:8000"

# CSS 스타일 (app copy.py 기반 + 개선)
st.markdown("""
<style>
    .main-score {
        font-size: 120px;
        font-weight: bold;
        text-align: center;
        padding: 30px;
        border-radius: 20px;
        margin: 20px 0;
    }
    .grade-text {
        font-size: 36px;
        text-align: center;
        font-weight: bold;
        margin-top: -20px;
    }
    .info-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin: 10px 0;
    }
    .recommendation-box {
        padding: 15px;
        border-radius: 10px;
        font-size: 18px;
        font-weight: 500;
        text-align: center;
        margin: 15px 0;
        border-left: 5px solid #2E86AB;
    }
    .main-header {
        font-size: 3rem;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #A23B72;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def get_api_status():
    """API 상태 확인"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200, response.json()
    except:
        return False, {"status": "disconnected"}

def predict_comfort_score(weather_data):
    """쾌적지수 예측 API 호출"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/predict",
            json=weather_data,
            timeout=10
        )
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, {"error": f"API 오류: {response.status_code}"}
    except Exception as e:
        return False, {"error": f"연결 오류: {str(e)}"}

def get_example_prediction():
    """예시 예측 결과 가져오기"""
    try:
        response = requests.get(f"{API_BASE_URL}/predict/example", timeout=10)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, {"error": f"API 오류: {response.status_code}"}
    except Exception as e:
        return False, {"error": f"연결 오류: {str(e)}"}

def get_comfort_grade(score):
    """쾌적지수 점수에 따른 등급 반환 (0-10 척도)"""
    if score >= 8.0:
        return "매우 쾌적", "#4CAF50"
    elif score >= 6.5:
        return "쾌적", "#8BC34A"
    elif score >= 5.0:
        return "보통", "#FFC107"
    elif score >= 3.5:
        return "불쾌", "#FF9800"
    else:
        return "매우 불쾌", "#F44336"

def get_recommendation(score, temp, pm10_grade, season):
    """점수에 따른 스마트 추천 메시지"""
    if score >= 8.0:
        return "🎉 외출하기 완벽한 날씨입니다! 야외활동을 즐겨보세요."
    elif score >= 6.5:
        return "😊 쾌적한 날씨입니다. 산책이나 운동하기 좋은 날입니다."
    elif score >= 5.0:
        return "😐 견딜만한 날씨입니다. 실내외 활동 모두 가능합니다."
    elif score >= 3.5:
        if pm10_grade in ['bad', 'very_bad']:
            return "😷 미세먼지가 나쁩니다. 마스크를 착용하고 외출하세요."
        elif temp < 5:
            return "🧥 날씨가 춥습니다. 따뜻하게 입고 나가세요."
        elif temp > 30:
            return "☀️ 날씨가 덥습니다. 수분 섭취를 충분히 하세요."
        else:
            return "🤔 불쾌한 날씨입니다. 실내 활동을 권장합니다."
    else:
        return "⚠️ 외출을 자제하고 실내에 머무르세요."

def get_temp_category(temperature):
    """온도에 따른 자동 카테고리 분류"""
    if temperature < 0:
        return "very_cold"
    elif temperature < 10:
        return "cold"
    elif temperature < 20:
        return "mild"
    elif temperature < 30:
        return "warm"
    else:
        return "hot"

def get_current_season():
    """현재 계절 자동 판단"""
    month = datetime.now().month
    if month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    elif month in [9, 10, 11]:
        return "autumn"
    else:
        return "winter"

# 메인 앱
def main():
    # 헤더
    st.markdown('<h1 class="main-header">🌤️ 날씨 쾌적지수 예측 시스템</h1>', unsafe_allow_html=True)
    st.markdown("**AI 기반 실시간 날씨 쾌적도 예측 서비스**")
    
    # API 상태 확인
    api_status, status_data = get_api_status()
    
    # 사이드바 - 시스템 상태 및 입력 폼
    with st.sidebar:
        st.markdown('<h2 class="sub-header">🔧 시스템 상태</h2>', unsafe_allow_html=True)
        
        if api_status:
            st.success("✅ API 서버 연결됨")
            if "model_status" in status_data:
                if status_data["model_status"] == "loaded":
                    st.success("✅ 모델 로드 완료")
                else:
                    st.error("❌ 모델 로드 실패")
        else:
            st.error("❌ API 서버 연결 실패")
            st.info("💡 Docker Compose로 API 서버를 먼저 실행해주세요")
            
        st.markdown("---")
        
        # 입력 폼 (슬라이더 기반)
        st.markdown('<h2 class="sub-header">📊 날씨 정보 입력</h2>', unsafe_allow_html=True)
        
        # 기본 날씨 정보
        st.subheader("🌡️ 기본 정보")
        temperature = st.slider("온도 (°C)", -20.0, 40.0, 20.0, 0.5)
        humidity = st.slider("습도 (%)", 0.0, 100.0, 65.0, 1.0)
        wind_speed = st.slider("풍속 (m/s)", 0.0, 30.0, 3.2, 0.5)
        
        # 상세 날씨 정보 (접을 수 있는 형태)
        with st.expander("🔍 상세 정보"):
            pressure = st.number_input("기압 (hPa)", 900.0, 1100.0, 1013.2)
            wind_direction = st.slider("풍향 (°)", 0.0, 360.0, 180.0, 10.0)
            dew_point = st.slider("이슬점 (°C)", -20.0, 30.0, 15.3, 0.5)
            cloud_amount = st.slider("운량 (0-10)", 0.0, 10.0, 5.0, 1.0)
            visibility = st.number_input("가시거리 (m)", 0.0, 20000.0, 10000.0, 100.0)
        
        # 시간 정보 (현재 시간 기반 자동 설정)
        st.subheader("⏰ 시간 정보")
        current_time = datetime.now()
        hour = st.slider("시간", 0, 23, current_time.hour)
        is_morning_rush = 1 if 7 <= hour <= 9 else 0
        is_evening_rush = 1 if 18 <= hour <= 20 else 0
        is_weekend = st.checkbox("주말", value=current_time.weekday() >= 5)
        
        # 계절 (자동 설정)
        season = st.selectbox("계절", ["spring", "summer", "autumn", "winter"], 
                             index=["spring", "summer", "autumn", "winter"].index(get_current_season()))
        
        # 미세먼지
        st.subheader("🌫️ 대기질")
        pm10_options = {
            "좋음": "good",
            "보통": "moderate", 
            "나쁨": "bad",
            "매우나쁨": "very_bad"
        }
        pm10_display = st.selectbox("미세먼지 등급", list(pm10_options.keys()))
        pm10_grade = pm10_options[pm10_display]
        
        # 지역 (수정된 옵션)
        st.subheader("📍 지역")
        region_options = {
            "중부": "central",
            "남부": "southern", 
            "기타": "unknown"
        }
        region_display = st.selectbox("지역 선택", list(region_options.keys()))
        region = region_options[region_display]
        
        # 예측 버튼
        predict_button = st.button("🔮 쾌적지수 예측", type="primary", use_container_width=True)
    
    # 메인 영역
    if not api_status:
        st.error("🚫 API 서버에 연결할 수 없습니다. 서버 상태를 확인해주세요.")
        return
    
    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["🎯 메인 예측", "📊 예시 결과", "ℹ️ 사용법"])
    
    with tab1:
        if predict_button:
            # 온도 카테고리 자동 분류
            temp_category = get_temp_category(temperature)
            
            # API 요청 데이터 구성
            weather_data = {
                "temperature": temperature,
                "humidity": humidity,
                "pressure": pressure,
                "wind_speed": wind_speed,
                "wind_direction": wind_direction,
                "dew_point": dew_point,
                "cloud_amount": cloud_amount,
                "visibility": visibility,
                "season": season,
                "temp_category": temp_category,
                "pm10_grade": pm10_grade,
                "region": region,
                "is_morning_rush": is_morning_rush,
                "is_evening_rush": is_evening_rush,
                "is_weekend": 1 if is_weekend else 0
            }
            
            try:
                # API 호출
                with st.spinner("쾌적지수 분석 중..."):
                    success, result = predict_comfort_score(weather_data)
                
                if success:
                    score = result["predicted_comfort_score"]
                    
                    # 등급과 색상
                    grade, color = get_comfort_grade(score)
                    
                    # 메인 점수 표시 (큰 화면)
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        st.markdown(f"""
                        <div class="main-score" style="background: linear-gradient(135deg, {color}22, {color}44); border: 5px solid {color};">
                            <span style="color: {color};">{score:.1f}</span>
                        </div>
                        <div class="grade-text" style="color: {color};">
                            {grade}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # 스마트 추천 메시지
                    recommendation = get_recommendation(score, temperature, pm10_grade, season)
                    st.markdown(f"""
                    <div class="recommendation-box" style="background-color: {color}22; border-left-color: {color};">
                        {recommendation}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 상세 정보 (메트릭 카드)
                    st.markdown("---")
                    st.subheader("📋 입력 정보 요약")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("🌡️ 온도", f"{temperature}°C")
                        st.metric("💧 습도", f"{humidity}%")
                        st.metric("💨 풍속", f"{wind_speed} m/s")
                    
                    with col2:
                        st.metric("⏰ 시간", f"{hour}시")
                        st.metric("🗓️ 요일", "주말" if is_weekend else "평일")
                        st.metric("🍂 계절", {"spring": "봄", "summer": "여름", "autumn": "가을", "winter": "겨울"}[season])
                    
                    with col3:
                        st.metric("🌫️ 미세먼지", pm10_display)
                        st.metric("📍 지역", region_display)
                        st.metric("🌡️ 온도구간", temp_category)
                
                else:
                    st.error(f"예측 실패: {result.get('error', '알 수 없는 오류')}")
            
            except Exception as e:
                st.error(f"❌ 오류 발생: {str(e)}")
        
        else:
            # 초기 화면
            st.info("👈 왼쪽 사이드바에서 날씨 정보를 입력하고 '쾌적지수 예측' 버튼을 눌러주세요.")
            
            # 쾌적지수 등급 안내
            with st.expander("💡 쾌적지수 등급 안내"):
                grade_info = pd.DataFrame({
                    "점수 범위": ["8.0-10", "6.5-7.9", "5.0-6.4", "3.5-4.9", "0-3.4"],
                    "등급": ["매우 쾌적", "쾌적", "보통", "불쾌", "매우 불쾌"],
                    "설명": [
                        "외출하기 완벽한 날씨",
                        "쾌적한 날씨, 야외활동 추천",
                        "견딜만한 날씨",
                        "불쾌한 날씨, 실내 활동 권장",
                        "매우 불쾌한 날씨, 외출 자제"
                    ]
                })
                st.table(grade_info)
    
    with tab2:
        st.markdown('<h2 class="sub-header">📊 예시 예측 결과</h2>', unsafe_allow_html=True)
        
        if st.button("🎲 예시 데이터로 예측해보기", type="secondary"):
            with st.spinner("예시 예측 중..."):
                success, result = get_example_prediction()
            
            if success:
                score = result["predicted_comfort_score"]
                grade, color = get_comfort_grade(score)
                
                # 예시 결과도 큰 화면으로 표시
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.markdown(f"""
                    <div class="main-score" style="background: linear-gradient(135deg, {color}22, {color}44); border: 5px solid {color};">
                        <span style="color: {color};">{score:.1f}</span>
                    </div>
                    <div class="grade-text" style="color: {color};">
                        {grade}
                    </div>
                    """, unsafe_allow_html=True)
                
                # 입력 데이터 표시
                st.markdown("**📝 사용된 입력 데이터:**")
                input_df = pd.DataFrame([result["input_data"]])
                st.dataframe(input_df, use_container_width=True)
                
            else:
                st.error(f"예시 예측 실패: {result.get('error', '알 수 없는 오류')}")
    
    with tab3:
        st.markdown('<h2 class="sub-header">ℹ️ 사용법 안내</h2>', unsafe_allow_html=True)
        
        st.markdown("""
        ### 🎯 쾌적지수란?
        - **0-10점 척도**로 날씨의 쾌적함 정도를 나타냅니다
        - **8점 이상**: 매우 쾌적한 날씨 🌟
        - **6.5-8점**: 쾌적한 날씨 😊
        - **5-6.5점**: 보통 날씨 😐
        - **3.5-5점**: 불쾌한 날씨 😕
        - **3.5점 미만**: 매우 불쾌한 날씨 😞
        
        ### 📊 스마트 기능
        - **자동 시간 설정**: 현재 시간 기반 출퇴근 시간대 자동 판단
        - **계절 자동 감지**: 현재 월 기준 계절 자동 설정
        - **온도 카테고리**: 입력 온도에 따른 자동 분류
        - **맞춤형 추천**: 날씨 조건별 개인화된 조언 제공
        
        ### 🚀 시스템 구성
        - **FastAPI**: 머신러닝 모델 서빙 API
        - **Streamlit**: 사용자 인터페이스
        - **AWS S3**: 모델 저장소
        - **Docker**: 컨테이너 환경
        
        ### 🔧 개발자 정보
        - **모델**: S3에서 자동으로 최고 성능 모델 로드
        - **전처리**: 학습 시와 동일한 전처리 파이프라인 적용
        - **API**: RESTful API로 예측 서비스 제공
        """)
    
    # 푸터
    st.markdown("---")
    st.caption("🤖 Powered by FastAPI + Streamlit + AWS S3 | Weather Comfort Prediction System")

if __name__ == "__main__":
    main() 