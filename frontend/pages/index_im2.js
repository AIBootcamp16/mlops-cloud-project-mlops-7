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

    // 백엔드에서 받은 label을 그대로 사용
    const scoreClass = result.label || 'fair';
    const emoji = result.score >= 80 ? '☀️' :
                 result.score >= 60 ? '😊' :
                 result.score >= 50 ? '😣' : '🥶';

    // 디버깅용
    console.log('Result:', result);
    console.log('Score Class:', scoreClass);
    console.log('Label:', result.label);

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
        
        {/* 상세 날씨 정보 */}
        {result.weather_data && (
          <div className="weather-details">
            <h3>📊 현재 날씨 정보</h3>
            <div className="weather-grid">
              <div className="weather-card">
                <div className="weather-icon">🌡️</div>
                <div className="weather-info">
                  <div className="weather-label">온도</div>
                  <div className="weather-value">{result.weather_data.temperature}°C</div>
                </div>
              </div>
              <div className="weather-card">
                <div className="weather-icon">💧</div>
                <div className="weather-info">
                  <div className="weather-label">습도</div>
                  <div className="weather-value">{result.weather_data.humidity}%</div>
                </div>
              </div>
              <div className="weather-card">
                <div className="weather-icon">🌧️</div>
                <div className="weather-info">
                  <div className="weather-label">강수량</div>
                  <div className="weather-value">{result.weather_data.precipitation}mm</div>
                </div>
              </div>
              <div className="weather-card">
                <div className="weather-icon">🌫️</div>
                <div className="weather-info">
                  <div className="weather-label">미세먼지</div>
                  <div className="weather-value">{result.weather_data.pm10}㎍/㎥</div>
                  <div className="weather-grade">({result.weather_data.pm10_grade})</div>
                </div>
              </div>
              <div className="weather-card">
                <div className="weather-icon">💨</div>
                <div className="weather-info">
                  <div className="weather-label">풍속</div>
                  <div className="weather-value">{result.weather_data.wind_speed}m/s</div>
                </div>
              </div>
              <div className="weather-card">
                <div className="weather-icon">🧭</div>
                <div className="weather-info">
                  <div className="weather-label">기압</div>
                  <div className="weather-value">{result.weather_data.pressure}hPa</div>
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
            transform: translateY(10px);
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

        .container {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
          max-width: 900px;
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

        /* 숫자 박스 색상 */
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
        }

        /* 등급 라벨 색상 */
        .score-label {
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

        /* 평가 박스 색상 */
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
          margin: 25px 0;
          animation: slideUp 0.9s ease-out;
        }

        .weather-details h3 {
          text-align: center;
          margin-bottom: 20px;
          font-size: 1.2em;
          font-weight: 600;
        }

        .weather-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
          gap: 12px;
        }

        .weather-card {
          background: rgba(255, 255, 255, 0.2);
          border-radius: 12px;
          padding: 15px;
          display: flex;
          align-items: center;
          gap: 12px;
          transition: all 0.3s ease;
          border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .weather-card:hover {
          background: rgba(255, 255, 255, 0.25);
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }

        .weather-icon {
          font-size: 2em;
          line-height: 1;
        }

        .weather-info {
          flex: 1;
        }

        .weather-label {
          font-size: 0.8em;
          opacity: 0.85;
          font-weight: 500;
          margin-bottom: 2px;
        }

        .weather-value {
          font-size: 1.1em;
          font-weight: 700;
        }

        .weather-grade {
          font-size: 0.75em;
          opacity: 0.8;
          margin-top: 2px;
        }

        .prediction-time {
          text-align: center;
          font-size: 0.9em;
          color: rgba(255, 255, 255, 0.8);
          margin-top: 25px;
          padding-top: 20px;
          border-top: 1px solid rgba(255, 255, 255, 0.2);
          font-weight: 300;
        }

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

          .weather-grid {
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 10px;
          }

          .weather-card {
            padding: 12px;
          }

          .result-box {
            padding: 25px 20px;
          }
        }

        @media (max-width: 480px) {
          .weather-grid {
            grid-template-columns: 1fr;
          }

          .score-number-box {
            padding: 25px 20px;
            font-size: 3.5em;
          }

          .score-label {
            font-size: 1.3em;
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