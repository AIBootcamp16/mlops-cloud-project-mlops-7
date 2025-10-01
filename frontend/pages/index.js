import { useState, useEffect, useRef } from 'react';

export default function Home() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [welcomeMessage, setWelcomeMessage] = useState('');
  const [showResult, setShowResult] = useState(false);
  const chartRef = useRef(null);
  const chartInstance = useRef(null);

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

  // Chart.js 초기화 및 업데이트
  useEffect(() => {
    if (!chartRef.current || !result || result.error) {
      return;
    }

    const loadChart = async () => {
      const Chart = (await import('chart.js')).Chart;
      await import('chart.js/auto');

      const ctx = chartRef.current.getContext('2d');
      const score = result.score || 0;
      const remaining = 100 - score;
      
      // 점수에 따른 색상 결정
      let color = '#FB8C00'; // fair
      if (score >= 80) color = '#FFB300'; // excellent
      else if (score >= 60) color = '#43A047'; // good
      else if (score < 50) color = '#E53935'; // poor

      if (chartInstance.current) {
        chartInstance.current.destroy();
      }

      chartInstance.current = new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: ['쾌적지수', ''],
          datasets: [{
            data: [score, remaining],
            backgroundColor: [color, 'rgba(255, 255, 255, 0.2)'],
            borderColor: 'rgba(255, 255, 255, 0.3)',
            borderWidth: 2,
            circumference: 360,
            rotation: -90
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
          cutout: '75%',
          animation: {
            animateRotate: true,
            duration: 2000,
            easing: 'easeInOutQuart'
          },
          plugins: {
            legend: {
              display: false
            },
            title: {
              display: false
            },
            tooltip: {
              enabled: false
            }
          }
        }
      });
    };

    loadChart();

    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, [result, showResult]);

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

    const scoreClass = (result.label || 'fair').toLowerCase();
    const displayLabel = result.label
      ? result.label.charAt(0).toUpperCase() + result.label.slice(1)
      : scoreClass.charAt(0).toUpperCase() + scoreClass.slice(1);
    const emoji = result.score >= 80 ? '☀️' :
                 result.score >= 60 ? '😊' :
                 result.score >= 50 ? '😣' : '🥶';

    return (
      <div className={`result-box ${showResult ? 'show' : ''}`}>
        {/* 쾌적 지수 섹션 - 원형 게이지 */}
        <div className="comfort-section">
          <h2 className="comfort-title">쾌적 지수</h2>
          
          <div className="gauge-container">
            <canvas ref={chartRef} width="300" height="300"></canvas>
            
            <div className="gauge-center">
              <div className={`gauge-score score-${scoreClass}`}>
                {result.score}
              </div>
              <div className={`gauge-label score-${scoreClass}`}>
                {displayLabel}
              </div>
              <div className="gauge-evaluation">
                <span className="emoji-small">{emoji}</span>
                {result.evaluation}
              </div>
            </div>
          </div>
        </div>
        
        {/* 간단한 한 줄 날씨 정보 */}
        {result.weather_data && (
          <div className="weather-details">
            <h2 className="weather-title">현재 날씨 정보</h2>
            <div className="weather-items">
              <div className="weather-item">
                <span className="weather-emoji">🌡️</span>
                <span className="weather-label">온도</span>
                <span className="weather-value">{result.weather_data.temperature}°C</span>
              </div>
              
              <div className="weather-item">
                <span className="weather-emoji">💧</span>
                <span className="weather-label">습도</span>
                <span className="weather-value">{result.weather_data.humidity}%</span>
              </div>
              
              <div className="weather-item">
                <span className="weather-emoji">🌧️</span>
                <span className="weather-label">강수량</span>
                <span className="weather-value">{result.weather_data.rainfall}mm</span>
              </div>
              
              <div className="weather-item">
                <span className="weather-emoji">🌫️</span>
                <span className="weather-label">미세먼지</span>
                <span className="weather-value">{result.weather_data.pm10}㎍/㎥</span>
              </div>
              
              <div className="weather-item">
                <span className="weather-emoji">💨</span>
                <span className="weather-label">풍속</span>
                <span className="weather-value">{result.weather_data.wind_speed}m/s</span>
              </div>
              
              <div className="weather-item">
                <span className="weather-emoji">🧭</span>
                <span className="weather-label">기압</span>
                <span className="weather-value">{result.weather_data.pressure}hPa</span>
              </div>
            </div>
          </div>
        )}
        
        <div className="prediction-time">
          📅 {new Date().toLocaleString('ko-KR', { 
            year: 'numeric', 
            month: '2-digit', 
            day: '2-digit', 
            hour: '2-digit', 
            minute: '2-digit',
            hour12: false 
          })}
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

        /* 원형 게이지 스타일 */
        .comfort-section {
          margin-bottom: 30px;
          animation: slideUp 0.6s ease-out;
        }

        .comfort-title {
          text-align: center;
          font-size: 1.3em;
          font-weight: 600;
          margin-bottom: 25px;
          color: white;
          text-shadow: 1px 1px 3px rgba(0,0,0,0.2);
        }

        .gauge-container {
          position: relative;
          width: 280px;
          height: 280px;
          margin: 0 auto 30px;
        }

        .gauge-center {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          text-align: center;
          z-index: 10;
          width: 100%;
        }

        .gauge-score {
          font-size: 5.5rem;
          font-weight: 800;
          line-height: 1;
          text-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
          margin-bottom: 5px;
        }

        .gauge-score.score-excellent {
          color: #FFB300;
        }

        .gauge-score.score-good {
          color: #43A047;
        }

        .gauge-score.score-fair {
          color: #FB8C00;
        }

        .gauge-score.score-poor {
          color: #E53935;
        }

        .gauge-label {
          font-size: 1.5rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 1px;
          margin-bottom: 10px;
        }

        .gauge-label.score-excellent {
          color: #FFB300;
        }

        .gauge-label.score-good {
          color: #43A047;
        }

        .gauge-label.score-fair {
          color: #FB8C00;
        }

        .gauge-label.score-poor {
          color: #E53935;
        }

        .gauge-evaluation {
          font-size: 0.95rem;
          font-weight: 600;
          color: white;
          margin-top: 8px;
          text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.3);
          line-height: 1.3;
          padding: 0 10px;
        }

        .emoji-small {
          font-size: 1.1em;
          margin-right: 3px;
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

        .weather-items {
          display: flex;
          flex-direction: column;
          gap: 15px;
          max-width: 600px;
          margin: 0 auto;
        }

        .weather-item {
          display: flex;
          align-items: center;
          gap: 15px;
          padding: 15px 20px;
          background: rgba(255, 255, 255, 0.15);
          border-radius: 12px;
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.2);
          transition: all 0.3s ease;
        }

        .weather-item:hover {
          background: rgba(255, 255, 255, 0.25);
          transform: translateX(5px);
        }

        .weather-emoji {
          font-size: 2em;
          flex-shrink: 0;
        }

        .weather-label {
          font-size: 1em;
          font-weight: 600;
          color: rgba(255, 255, 255, 0.9);
          min-width: 60px;
          flex-shrink: 0;
        }

        .weather-value {
          font-size: 1.1em;
          font-weight: 700;
          color: white;
          text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
          margin-left: auto;
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

          .gauge-container {
            width: 240px;
            height: 240px;
          }

          .gauge-score {
            font-size: 4rem;
          }

          .gauge-label {
            font-size: 1.3rem;
          }

          .gauge-evaluation {
            font-size: 0.85rem;
          }

          .weather-title {
            font-size: 1.3em;
            margin-bottom: 25px;
          }
        }

        @media (max-width: 480px) {
          .gauge-container {
            width: 200px;
            height: 200px;
          }

          .gauge-score {
            font-size: 3.5rem;
          }

          .gauge-label {
            font-size: 1.1rem;
          }

          .gauge-evaluation {
            font-size: 0.8rem;
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