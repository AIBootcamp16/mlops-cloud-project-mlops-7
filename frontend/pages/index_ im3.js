import { useState, useEffect } from 'react';

export default function Home() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [welcomeMessage, setWelcomeMessage] = useState('');
  const [showResult, setShowResult] = useState(false);

  // FastAPI 서버 URL (Docker 환경)
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // 백엔드에서 환영 메시지 가져오기
  useEffect(() => {
    const fetchWelcomeMessage = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/welcome`);
        const data = await response.json();
        if (response.ok) {
          setWelcomeMessage(data.message);
        } else {
          setWelcomeMessage("안녕하세요! 😊<br/>날씨 예측 서비스입니다!");
        }
      } catch (error) {
        console.log("환영 메시지 로드 실패:", error);
        setWelcomeMessage("안녕하세요! 😊<br/>날씨 예측 서비스입니다!");
      }
    };

    fetchWelcomeMessage();
  }, [API_BASE_URL]);

  // 예측 API 호출
  const getPrediction = async (type) => {
    setLoading(true);
    setResult(null);
    setShowResult(false);

    try {
      const response = await fetch(`${API_BASE_URL}/predict/${type}`);
      const data = await response.json();

      if (response.ok) {
        setResult(data);
        setTimeout(() => setShowResult(true), 100);
      } else {
        setResult({ error: `API 오류: ${response.status}`, details: data.detail });
        setTimeout(() => setShowResult(true), 100);
      }
    } catch (error) {
      setResult({ error: `네트워크 오류: ${error.message}` });
      setTimeout(() => setShowResult(true), 100);
    } finally {
      setLoading(false);
    }
  };

  // 온도에 따른 색상 계산
  const getTemperatureColor = (temp) => {
    if (temp >= 30) return '#FF6B6B';
    if (temp >= 25) return '#FF9F43';
    if (temp >= 20) return '#FFA500';
    if (temp >= 15) return '#54A0FF';
    if (temp >= 10) return '#5F9ED1';
    return '#4A90E2';
  };

  // 습도에 따른 색상
  const getHumidityColor = (humidity) => {
    if (humidity >= 70) return '#3498DB';
    if (humidity >= 50) return '#5DADE2';
    return '#85C1E9';
  };

  // 미세먼지 등급에 따른 색상
  const getPM10Color = (pm10) => {
    if (pm10 <= 30) return '#4CAF50';
    if (pm10 <= 80) return '#8BC34A';
    if (pm10 <= 150) return '#FF9800';
    return '#F44336';
  };

  // 강수량에 따른 색상
  const getPrecipitationColor = (precip) => {
    if (precip === 0) return '#BDC3C7';
    if (precip < 5) return '#5DADE2';
    if (precip < 20) return '#3498DB';
    return '#2874A6';
  };

  // 풍속에 따른 색상
  const getWindColor = (wind) => {
    if (wind >= 10) return '#E74C3C';
    if (wind >= 5) return '#F39C12';
    return '#00BCD4';
  };

  // 기압 색상
  const getPressureColor = () => '#8BC34A';

  // 결과 표시 컴포넌트
  const ResultDisplay = () => {
    if (loading) {
      return (
        <div className="result-box">
          <div className="loading-spinner"></div>
          <div className="loading">예측 중...</div>
        </div>
      );
    }

    if (!result) {
      return (
        <div className="result-box welcome">
          <div className="welcome-icon">🌤️</div>
          <div className="loading" dangerouslySetInnerHTML={{ __html: welcomeMessage }} />
        </div>
      );
    }

    if (result.error) {
      return (
        <div className={`result-box ${showResult ? 'show' : ''}`}>
          <div className="error-icon">⚠️</div>
          <div className="error">{result.error}</div>
          {result.details && <div className="error-details">{result.details}</div>}
        </div>
      );
    }

    const scoreClass = result.label || 'fair';
    const emoji = result.score >= 80 ? '☀️' :
                 result.score >= 60 ? '😊' :
                 result.score >= 50 ? '😣' : '🥶';

    return (
      <div className={`result-box ${showResult ? 'show' : ''}`}>
        {/* 쾌적 지수 섹션 */}
        <div className="comfort-section">
          <h2 className="comfort-title">쾌적 지수</h2>
          <div className={`score-number-box score-${scoreClass}`}>
            {result.score}
          </div>
          <div className="score-label">{result.label}</div>
        </div>

        {/* 평가 메시지 박스 */}
        <div className={`evaluation-box eval-${scoreClass}`}>
          <span className="emoji-inline">{emoji}</span>
          {result.evaluation}
        </div>
        
        {/* 상세 날씨 정보 - 개선된 버전 */}
        {result.weather_data && (
          <div className="weather-details">
            <h3 className="weather-title">📊 현재 날씨 정보</h3>
            <div className="weather-grid-new">
              {/* 온도 카드 */}
              <div 
                className="weather-card-new temp-card-new"
                style={{ 
                  '--card-color': getTemperatureColor(result.weather_data.temperature),
                  animationDelay: '0.1s'
                }}
              >
                <div className="card-icon">🌡️</div>
                <div className="card-content">
                  <div className="card-label">온도</div>
                  <div className="card-value">{result.weather_data.temperature}°C</div>
                </div>
              </div>
              
              {/* 습도 카드 */}
              <div 
                className="weather-card-new humidity-card-new"
                style={{ 
                  '--card-color': getHumidityColor(result.weather_data.humidity),
                  animationDelay: '0.15s'
                }}
              >
                <div className="card-icon">💧</div>
                <div className="card-content">
                  <div className="card-label">습도</div>
                  <div className="card-value">{result.weather_data.humidity}%</div>
                </div>
              </div>
              
              {/* 미세먼지 카드 - 강조 */}
              <div 
                className="weather-card-new pm-card-new featured"
                style={{ 
                  '--card-color': getPM10Color(result.weather_data.pm10),
                  animationDelay: '0.2s'
                }}
              >
                <div className="card-icon">🌫️</div>
                <div className="card-content">
                  <div className="card-label">미세먼지</div>
                  <div className="card-value">{result.weather_data.pm10}<span className="unit">㎍/㎥</span></div>
                  <div className="card-grade">{result.weather_data.pm10_grade}</div>
                </div>
              </div>
              
              {/* 강수량 카드 */}
              <div 
                className="weather-card-new rain-card-new"
                style={{ 
                  '--card-color': getPrecipitationColor(result.weather_data.precipitation),
                  animationDelay: '0.25s'
                }}
              >
                <div className="card-icon">🌧️</div>
                <div className="card-content">
                  <div className="card-label">강수량</div>
                  <div className="card-value">{result.weather_data.precipitation}<span className="unit">mm</span></div>
                </div>
              </div>
              
              {/* 풍속 카드 */}
              <div 
                className="weather-card-new wind-card-new"
                style={{ 
                  '--card-color': getWindColor(result.weather_data.wind_speed),
                  animationDelay: '0.3s'
                }}
              >
                <div className="card-icon">💨</div>
                <div className="card-content">
                  <div className="card-label">풍속</div>
                  <div className="card-value">{result.weather_data.wind_speed}<span className="unit">m/s</span></div>
                </div>
              </div>
              
              {/* 기압 카드 */}
              <div 
                className="weather-card-new pressure-card-new"
                style={{ 
                  '--card-color': getPressureColor(),
                  animationDelay: '0.35s'
                }}
              >
                <div className="card-icon">🧭</div>
                <div className="card-content">
                  <div className="card-label">기압</div>
                  <div className="card-value">{result.weather_data.pressure}<span className="unit">hPa</span></div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div className="prediction-time">
          📅 {result.prediction_time}
        </div>
      </div>
    );
  };

  return (
    <>
      <div className="container">
        <header className="header">
          <div className="header-icon">🌤️</div>
          <h1>출퇴근길 날씨 친구</h1>
          <p className="subtitle">실시간 쾌적지수 예측 서비스</p>
        </header>

        <div className="buttons">
          <button className="btn-primary" onClick={() => getPrediction('now')}>
            <span className="btn-icon">📱</span>
            <span className="btn-text">지금 날씨</span>
          </button>
          <button className="btn-primary" onClick={() => getPrediction('morning')}>
            <span className="btn-icon">🌅</span>
            <span className="btn-text">출근길 예측</span>
          </button>
          <button className="btn-primary" onClick={() => getPrediction('evening')}>
            <span className="btn-icon">🌆</span>
            <span className="btn-text">퇴근길 예측</span>
          </button>
        </div>

        <ResultDisplay />
      </div>

      <style jsx>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.05); }
        }

        @keyframes cardFloat {
          from {
            opacity: 0;
            transform: translateY(30px) scale(0.95);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }

        .container {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
          max-width: 1000px;
          margin: 0 auto;
          padding: 30px 20px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          min-height: 100vh;
          color: white;
        }

        .header {
          text-align: center;
          margin-bottom: 40px;
          animation: fadeIn 0.6s ease-out;
        }

        .header-icon {
          font-size: 4em;
          margin-bottom: 10px;
          animation: pulse 2s ease-in-out infinite;
        }

        h1 {
          font-size: 2.5em;
          margin: 10px 0;
          font-weight: 700;
          text-shadow: 2px 2px 8px rgba(0,0,0,0.3);
          letter-spacing: -0.5px;
        }

        .subtitle {
          font-size: 1em;
          opacity: 0.9;
          font-weight: 300;
          margin-top: 5px;
        }

        .buttons {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 15px;
          margin-bottom: 35px;
        }

        .btn-primary {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
          padding: 18px 30px;
          font-size: 17px;
          font-weight: 600;
          border: none;
          border-radius: 15px;
          background: rgba(255, 255, 255, 0.25);
          color: white;
          cursor: pointer;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          backdrop-filter: blur(10px);
          border: 2px solid rgba(255, 255, 255, 0.3);
          position: relative;
          overflow: hidden;
        }

        .btn-primary::before {
          content: '';
          position: absolute;
          top: 50%;
          left: 50%;
          width: 0;
          height: 0;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.3);
          transform: translate(-50%, -50%);
          transition: width 0.6s, height 0.6s;
        }

        .btn-primary:hover::before {
          width: 300px;
          height: 300px;
        }

        .btn-primary:hover {
          background: rgba(255, 255, 255, 0.35);
          transform: translateY(-3px);
          box-shadow: 0 10px 25px rgba(0,0,0,0.3);
          border-color: rgba(255, 255, 255, 0.5);
        }

        .btn-primary:active {
          transform: translateY(-1px);
        }

        .btn-icon {
          font-size: 1.5em;
          position: relative;
          z-index: 1;
        }

        .btn-text {
          position: relative;
          z-index: 1;
        }

        .result-box {
          background: rgba(255, 255, 255, 0.2);
          border-radius: 20px;
          padding: 35px 30px;
          backdrop-filter: blur(20px);
          box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
          border: 1px solid rgba(255, 255, 255, 0.18);
          opacity: 0;
          animation: fadeIn 0.5s ease-out forwards;
        }

        .result-box.show {
          animation: fadeIn 0.5s ease-out forwards;
        }

        .result-box.welcome {
          text-align: center;
          padding: 50px 30px;
        }

        .welcome-icon {
          font-size: 5em;
          margin-bottom: 20px;
          animation: pulse 2s ease-in-out infinite;
        }

        .loading-spinner {
          width: 50px;
          height: 50px;
          border: 4px solid rgba(255, 255, 255, 0.3);
          border-top-color: white;
          border-radius: 50%;
          margin: 0 auto 20px;
          animation: spin 1s linear infinite;
        }

        .loading {
          text-align: center;
          color: rgba(255, 255, 255, 0.9);
          font-size: 18px;
          line-height: 1.6;
          font-weight: 300;
        }

        .error-icon {
          font-size: 3em;
          text-align: center;
          margin-bottom: 15px;
        }

        .error {
          color: #FFE0E0;
          text-align: center;
          font-size: 1.2em;
          font-weight: 600;
          margin-bottom: 10px;
        }

        .error-details {
          color: #FFD4A3;
          text-align: center;
          font-size: 0.95em;
          opacity: 0.9;
        }

        .comfort-section {
          margin-bottom: 30px;
          animation: slideUp 0.6s ease-out;
        }

        .comfort-title {
          text-align: center;
          font-size: 1.3em;
          font-weight: 600;
          margin-bottom: 15px;
          color: white;
          text-shadow: 1px 1px 3px rgba(0,0,0,0.2);
        }

        .score-number-box {
          max-width: 400px;
          margin: 0 auto 15px;
          padding: 40px 30px;
          backdrop-filter: blur(10px);
          border-radius: 20px;
          text-align: center;
          box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
          font-size: 6em;
          font-weight: 800;
          line-height: 1;
          letter-spacing: -2px;
          transition: all 0.3s ease;
        }

        .score-number-box.score-excellent {
          background: linear-gradient(135deg, rgba(255, 215, 0, 0.2), rgba(255, 215, 0, 0.35));
          border: 5px solid #FFD700;
          color: #FFD700;
        }

        .score-number-box.score-good {
          background: linear-gradient(135deg, rgba(76, 175, 80, 0.2), rgba(76, 175, 80, 0.35));
          border: 5px solid #4CAF50;
          color: #4CAF50;
        }

        .score-number-box.score-fair {
          background: linear-gradient(135deg, rgba(255, 152, 0, 0.2), rgba(255, 152, 0, 0.35));
          border: 5px solid #FF9800;
          color: #FF9800;
        }

        .score-number-box.score-poor {
          background: linear-gradient(135deg, rgba(244, 67, 54, 0.2), rgba(244, 67, 54, 0.35));
          border: 5px solid #F44336;
          color: #F44336;
        }

        .score-label {
          text-align: center;
          font-size: 1.8em;
          font-weight: 700;
          margin-bottom: 25px;
          text-transform: lowercase;
          color: white;
        }

        .evaluation-box {
          max-width: 650px;
          margin: 0 auto 35px;
          padding: 25px 30px;
          border-radius: 15px;
          border-left: 6px solid;
          text-align: left;
          font-size: 1.15em;
          line-height: 1.6;
          color: #333;
          box-shadow: 0 4px 12px rgba(0,0,0,0.1);
          animation: slideUp 0.8s ease-out;
          transition: all 0.3s ease;
        }

        .evaluation-box.eval-excellent {
          background-color: rgba(255, 215, 0, 0.15);
          border-left-color: #FFD700;
        }

        .evaluation-box.eval-good {
          background-color: rgba(76, 175, 80, 0.15);
          border-left-color: #4CAF50;
        }

        .evaluation-box.eval-fair {
          background-color: rgba(255, 152, 0, 0.15);
          border-left-color: #FF9800;
        }

        .evaluation-box.eval-poor {
          background-color: rgba(244, 67, 54, 0.15);
          border-left-color: #F44336;
        }

        .emoji-inline {
          font-size: 1.4em;
          margin-right: 10px;
        }

        .weather-details {
          margin: 30px 0;
          animation: slideUp 0.9s ease-out;
        }

        .weather-title {
          text-align: center;
          margin-bottom: 30px;
          font-size: 1.5em;
          font-weight: 700;
          text-shadow: 2px 2px 6px rgba(0,0,0,0.3);
          letter-spacing: 0.5px;
        }

        /* 새로운 날씨 그리드 */
        .weather-grid-new {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
          gap: 20px;
          max-width: 900px;
          margin: 0 auto;
        }

        /* 새로운 날씨 카드 */
        .weather-card-new {
          background: rgba(255, 255, 255, 0.15);
          backdrop-filter: blur(15px);
          border: 3px solid rgba(255, 255, 255, 0.25);
          border-radius: 20px;
          padding: 30px 20px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 15px;
          transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
          cursor: pointer;
          position: relative;
          overflow: hidden;
          opacity: 0;
          animation: cardFloat 0.6s ease-out forwards;
          box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
        }

        .weather-card-new::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: linear-gradient(135deg, var(--card-color), transparent);
          opacity: 0;
          transition: opacity 0.4s ease;
          border-radius: 20px;
        }

        .weather-card-new:hover {
          transform: translateY(-8px) scale(1.03);
          box-shadow: 0 15px 35px rgba(0, 0, 0, 0.25);
          border-color: var(--card-color);
        }

        .weather-card-new:hover::before {
          opacity: 0.2;
        }

        /* 강조 카드 (온도, 미세먼지) */
        .weather-card-new.featured {
          grid-column: span 1;
          background: rgba(255, 255, 255, 0.2);
        }

        .card-icon {
          font-size: 4em;
          filter: drop-shadow(3px 3px 6px rgba(0,0,0,0.3));
          transition: transform 0.4s ease;
          position: relative;
          z-index: 1;
        }

        .weather-card-new:hover .card-icon {
          transform: scale(1.15) rotate(5deg);
        }

        .card-content {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
          position: relative;
          z-index: 1;
        }

        .card-label {
          font-size: 0.95em;
          font-weight: 600;
          color: rgba(255, 255, 255, 0.85);
          text-transform: uppercase;
          letter-spacing: 1px;
        }

        .card-value {
          font-size: 2.2em;
          font-weight: 900;
          color: white;
          text-shadow: 2px 2px 8px rgba(0,0,0,0.4);
          line-height: 1;
          letter-spacing: -1px;
        }

        .card-value .unit {
          font-size: 0.5em;
          font-weight: 600;
          margin-left: 3px;
          opacity: 0.8;
        }

        .card-grade {
          font-size: 0.85em;
          padding: 4px 12px;
          background: rgba(255, 255, 255, 0.25);
          border-radius: 12px;
          font-weight: 600;
          color: white;
          backdrop-filter: blur(5px);
        }

        .prediction-time {
          text-align: center;
          font-size: 0.9em;
          color: rgba(255, 255, 255, 0.8);
          margin-top: 30px;
          padding-top: 20px;
          border-top: 1px solid rgba(255, 255, 255, 0.2);
          font-weight: 300;
        }

        /* 반응형 디자인 */
        @media (max-width: 768px) {
          .container {
            padding: 20px 15px;
          }
          
          .header-icon {
            font-size: 3em;
          }

          h1 {
            font-size: 2em;
          }

          .subtitle {
            font-size: 0.9em;
          }
          
          .buttons {
            grid-template-columns: 1fr;
            gap: 12px;
          }
          
          .btn-primary {
            padding: 16px 25px;
            font-size: 16px;
          }

          .score-number-box {
            padding: 30px 25px;
            font-size: 4.5em;
          }

          .score-label {
            font-size: 1.5em;
          }

          .evaluation-box {
            font-size: 1em;
            padding: 20px 25px;
          }

          .weather-title {
            font-size: 1.3em;
            margin-bottom: 25px;
          }

          .weather-grid-new {
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
          }

          .weather-card-new {
            padding: 25px 15px;
          }

          .card-icon {
            font-size: 3em;
          }

          .card-value {
            font-size: 1.8em;
          }
        }

        @media (max-width: 480px) {
          .weather-grid-new {
            grid-template-columns: 1fr;
            gap: 12px;
          }

          .weather-card-new {
            padding: 25px 20px;
          }

          .weather-card-new.featured {
            grid-column: span 1;
          }

          .card-icon {
            font-size: 3.5em;
          }

          .card-value {
            font-size: 2em;
          }

          .score-number-box {
            padding: 25px 20px;
            font-size: 3.5em;
          }

          .score-label {
            font-size: 1.3em;
          }
        }

        /* 데스크톱 3열 레이아웃 */
        @media (min-width: 900px) {
          .weather-grid-new {
            grid-template-columns: repeat(3, 1fr);
          }
        }
      `}</style>

      <style jsx global>{`
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }

        html, body {
          height: 100%;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        }

        #__next {
          height: 100%;
        }
      `}</style>
    </>
  );
}