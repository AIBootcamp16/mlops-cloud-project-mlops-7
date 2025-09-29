import streamlit as st
import requests
import json
import pandas as pd

# 페이지 설정
st.set_page_config(
    page_title="🌤️ 날씨 쾌적지수 예측기",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 스타일링
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #A23B72;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #2E86AB;
    }
    .prediction-result {
        font-size: 2rem;
        font-weight: bold;
        text-align: center;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .good-score {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    .moderate-score {
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffeaa7;
    }
    .bad-score {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f1b0b7;
    }
</style>
""", unsafe_allow_html=True)

# API 엔드포인트 (Docker Compose 환경에서는 서비스명 사용)
API_BASE_URL = "http://api-server:8000"

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

def get_score_interpretation(score):
    """점수 해석 및 스타일 클래스 반환"""
    if score >= 7.0:
        return "매우 쾌적", "good-score", "🌟"
    elif score >= 6.0:
        return "쾌적", "good-score", "😊"
    elif score >= 5.0:
        return "보통", "moderate-score", "😐"
    elif score >= 4.0:
        return "다소 불쾌", "moderate-score", "😕"
    else:
        return "불쾌", "bad-score", "😞"

# 메인 앱
def main():
    # 헤더
    st.markdown('<h1 class="main-header">🌤️ 날씨 쾌적지수 예측기</h1>', unsafe_allow_html=True)
    st.markdown("**머신러닝 모델을 활용한 실시간 날씨 쾌적도 예측 서비스**")
    
    # API 상태 확인
    api_status, status_data = get_api_status()
    
    # 사이드바 - API 상태
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
            st.info("💡 Docker Compose로 API 서버를 먼저 실행해주세요:\n```bash\ndocker-compose up api-server\n```")
    
    # 메인 컨텐츠
    if not api_status:
        st.error("🚫 API 서버에 연결할 수 없습니다. 서버 상태를 확인해주세요.")
        return
    
    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["🎯 예측하기", "📊 예시 결과", "ℹ️ 사용법"])
    
    with tab1:
        st.markdown('<h2 class="sub-header">날씨 정보 입력</h2>', unsafe_allow_html=True)
        
        # 입력 폼을 두 개의 컬럼으로 나누기
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🌡️ 기본 날씨 정보**")
            temperature = st.number_input("온도 (°C)", min_value=-30.0, max_value=50.0, value=20.5, step=0.1)
            humidity = st.number_input("습도 (%)", min_value=0.0, max_value=100.0, value=65.0, step=1.0)
            pressure = st.number_input("기압 (hPa)", min_value=900.0, max_value=1100.0, value=1013.2, step=0.1)
            wind_speed = st.number_input("풍속 (m/s)", min_value=0.0, max_value=50.0, value=3.2, step=0.1)
            wind_direction = st.number_input("풍향 (도)", min_value=0.0, max_value=360.0, value=180.0, step=1.0)
            
        with col2:
            st.markdown("**🌫️ 상세 날씨 정보**")
            dew_point = st.number_input("이슬점 (°C)", min_value=-30.0, max_value=30.0, value=15.3, step=0.1)
            cloud_amount = st.number_input("운량 (0-10)", min_value=0.0, max_value=10.0, value=5.0, step=0.1)
            visibility = st.number_input("가시거리 (m)", min_value=0.0, max_value=20000.0, value=10000.0, step=100.0)
            
            # 범주형 변수들
            season = st.selectbox("계절", ["spring", "summer", "autumn", "winter"], index=0)
            temp_category = st.selectbox("온도 범주", ["very_cold", "cold", "mild", "warm", "hot"], index=2)
            pm10_grade = st.selectbox("미세먼지 등급", ["good", "moderate", "bad", "very_bad"], index=0)
            region = st.selectbox("지역", ["central", "southern", "unknown"], index=0)
        
        # 시간대 정보
        st.markdown("**⏰ 시간대 정보**")
        time_col1, time_col2, time_col3 = st.columns(3)
        
        with time_col1:
            is_morning_rush = st.checkbox("출근시간대 (7-9시)", value=False)
        with time_col2:
            is_evening_rush = st.checkbox("퇴근시간대 (17-19시)", value=False)
        with time_col3:
            is_weekend = st.checkbox("주말", value=True)
        
        # 예측 버튼
        if st.button("🔮 쾌적지수 예측하기", type="primary", use_container_width=True):
            # 입력 데이터 구성
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
                "is_morning_rush": int(is_morning_rush),
                "is_evening_rush": int(is_evening_rush),
                "is_weekend": int(is_weekend)
            }
            
            # 예측 수행
            with st.spinner("예측 중..."):
                success, result = predict_comfort_score(weather_data)
            
            if success:
                score = result["predicted_comfort_score"]
                interpretation, css_class, emoji = get_score_interpretation(score)
                
                # 결과 표시
                st.markdown(f"""
                <div class="prediction-result {css_class}">
                    {emoji} 예측 쾌적지수: {score}/10<br>
                    <small>{interpretation}</small>
                </div>
                """, unsafe_allow_html=True)
                
                # 상세 정보
                with st.expander("📋 상세 결과 보기"):
                    st.json(result)
                    
            else:
                st.error(f"예측 실패: {result.get('error', '알 수 없는 오류')}")
    
    with tab2:
        st.markdown('<h2 class="sub-header">📊 예시 예측 결과</h2>', unsafe_allow_html=True)
        
        if st.button("🎲 예시 데이터로 예측해보기", type="secondary"):
            with st.spinner("예시 예측 중..."):
                success, result = get_example_prediction()
            
            if success:
                score = result["predicted_comfort_score"]
                interpretation, css_class, emoji = get_score_interpretation(score)
                
                st.markdown(f"""
                <div class="prediction-result {css_class}">
                    {emoji} 예측 쾌적지수: {score}/10<br>
                    <small>{interpretation}</small>
                </div>
                """, unsafe_allow_html=True)
                
                # 입력 데이터 표시
                st.markdown("**📝 사용된 입력 데이터:**")
                input_df = pd.DataFrame([result["input_data"]])
                st.dataframe(input_df, use_container_width=True)
                
                # 모델 정보
                st.info(f"🤖 모델: {result.get('model_info', 'Unknown')}")
                
            else:
                st.error(f"예시 예측 실패: {result.get('error', '알 수 없는 오류')}")
    
    with tab3:
        st.markdown('<h2 class="sub-header">ℹ️ 사용법 안내</h2>', unsafe_allow_html=True)
        
        st.markdown("""
        ### 🎯 쾌적지수란?
        - **0-10점 척도**로 날씨의 쾌적함 정도를 나타냅니다
        - **7점 이상**: 매우 쾌적한 날씨 🌟
        - **6-7점**: 쾌적한 날씨 😊
        - **5-6점**: 보통 날씨 😐
        - **4-5점**: 다소 불쾌한 날씨 😕
        - **4점 미만**: 불쾌한 날씨 😞
        
        ### 📊 입력 변수 설명
        
        **🌡️ 기본 날씨 정보**
        - **온도**: 현재 기온 (섭씨)
        - **습도**: 상대습도 (%)
        - **기압**: 해면기압 (hPa)
        - **풍속**: 평균 풍속 (m/s)
        - **풍향**: 바람이 불어오는 방향 (도, 0=북쪽)
        
        **🌫️ 상세 정보**
        - **이슬점**: 공기 중 수증기가 응결되기 시작하는 온도
        - **운량**: 하늘을 덮는 구름의 양 (0-10, 10이 완전히 흐림)
        - **가시거리**: 수평 가시거리 (m)
        - **미세먼지**: PM10 농도 등급
        
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

if __name__ == "__main__":
    main() 