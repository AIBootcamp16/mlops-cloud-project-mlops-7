import { useState, useEffect } from 'react';
import Head from 'next/head';

export default function Home() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [welcomeMessage, setWelcomeMessage] = useState('');

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

    try {
      const response = await fetch(`${API_BASE_URL}/predict/${type}`);
      const data = await response.json();

      if (response.ok) {
        setResult(data);
      } else {
        setResult({ error: `API 오류: ${response.status}`, details: data.detail });
      }
    } catch (error) {
      setResult({ error: `네트워크 오류: ${error.message}` });
    } finally {
      setLoading(false);
    }
  };

  // 결과 표시 컴포넌트
  const ResultDisplay = () => {
    if (loading) {
      return (
        <div className="result-box">
          <div className="loading">⏳ 예측 중...</div>
        </div>
      );
    }

    if (!result) {
      return (
        <div className="result-box">
          <div className="loading" dangerouslySetInnerHTML={{ __html: welcomeMessage }} />
        </div>
      );
    }

    if (result.error) {
      return (
        <div className="result-box">
          <div className="error">❌ {result.error}</div>
          {result.details && <div className="error-details">{result.details}</div>}
        </div>
      );
    }

    // 백엔드에서 받은 label을 그대로 사용
    const scoreClass = result.label || 'fair';

    const emoji = result.score >= 80 ? '☀️' :
                 result.score >= 60 ? '😊' :
                 result.score >= 50 ? '😣' : '🥶';

    const scoreIcon = result.score >= 60 ? '🌟' : '⚠️';

    return (
      <div className="result-box">
        <div className={`score ${scoreClass}`}>
          {scoreIcon} {result.score}/100 ({result.label})
        </div>
        <div className="evaluation">
          {result.evaluation} {emoji}
        </div>
        
        {/* 상세 날씨 정보 */}
        {result.weather_data && (
          <div className="weather-details">
            <h3>📊 현재 날씨 정보</h3>
            <div className="weather-grid">
              <div className="weather-item">
                <span className="label">🌡️ 온도:</span>
                <span className="value">{result.weather_data.temperature}°C</span>
              </div>
              <div className="weather-item">
                <span className="label">💧 습도:</span>
                <span className="value">{result.weather_data.humidity}%</span>
              </div>
              <div className="weather-item">
                <span className="label">🌧️ 강수량:</span>
                <span className="value">{result.weather_data.precipitation}mm</span>
              </div>
              <div className="weather-item">
                <span className="label">🌫️ 미세먼지:</span>
                <span className="value">{result.weather_data.pm10}㎍/㎥ ({result.weather_data.pm10_grade})</span>
              </div>
              <div className="weather-item">
                <span className="label">💨 풍속:</span>
                <span className="value">{result.weather_data.wind_speed}m/s</span>
              </div>
              <div className="weather-item">
                <span className="label">🧭 기압:</span>
                <span className="value">{result.weather_data.pressure}hPa</span>
              </div>
            </div>
          </div>
        )}
        
        <div className="prediction-time">
          📅 예측 시간: {result.prediction_time}
        </div>
      </div>
    );
  };

  return (
    <>
      <Head>
        <title>출퇴근길 날씨 친구</title>
        <meta name="description" content="기상청 데이터 기반 실시간 출퇴근 쾌적지수 예측 서비스" />
        <meta name="theme-color" content="#4A90E2" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="apple-mobile-web-app-title" content="날씨친구" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
        
        {/* PWA 매니페스트 */}
        <link rel="manifest" href="/manifest.json" />
        <link rel="apple-touch-icon" href="/icon-192x192.png" />
      </Head>

      <div className="container">
        <h1>🌤️ 출퇴근길 날씨 친구</h1>

        <div className="buttons">
          <button onClick={() => getPrediction('now')}>
            📱 지금 날씨
          </button>
          <button onClick={() => getPrediction('morning')}>
            🌅 출근길 예측
          </button>
          <button onClick={() => getPrediction('evening')}>
            🌆 퇴근길 예측
          </button>
        </div>

        <ResultDisplay />
      </div>

      <style jsx>{`
        .container {
          font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
          max-width: 800px;
          margin: 0 auto;
          padding: 20px;
          background: linear-gradient(135deg, #4A90E2 0%, #2E86AB 100%);
          min-height: 100vh;
          color: white;
        }

        h1 {
          text-align: center;
          margin-bottom: 30px;
          font-size: 2.5em;
          text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .buttons {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 20px;
          margin-bottom: 30px;
        }

        button {
          padding: 15px 25px;
          font-size: 16px;
          border: none;
          border-radius: 10px;
          background: rgba(255, 255, 255, 0.2);
          color: white;
          cursor: pointer;
          transition: all 0.3s ease;
          backdrop-filter: blur(5px);
        }

        button:hover {
          background: rgba(255, 255, 255, 0.3);
          transform: translateY(-2px);
          box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }

        button:active {
          transform: translateY(0);
        }

        .result-box {
          background: rgba(255, 255, 255, 0.15);
          border-radius: 15px;
          padding: 20px;
          margin-top: 20px;
          min-height: 100px;
          backdrop-filter: blur(10px);
          box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        }

        .loading {
          text-align: center;
          color: #ccc;
          font-size: 18px;
          line-height: 1.6;
        }

        .score {
          font-size: 2em;
          font-weight: bold;
          text-align: center;
          margin: 20px 0;
        }

        .excellent { 
          color: #FFD700; 
          text-shadow: 1px 1px 2px rgba(0,0,0,0.5); 
        }
        
        .good { 
          color: #90EE90; 
          text-shadow: 1px 1px 2px rgba(0,0,0,0.5); 
        }
        
        .fair { 
          color: #FFA500; 
          text-shadow: 1px 1px 2px rgba(0,0,0,0.5); 
        }
        
        .poor { 
          color: #FF6B6B; 
          text-shadow: 1px 1px 2px rgba(0,0,0,0.5); 
        }

        .evaluation {
          text-align: center;
          font-size: 1.2em;
          margin: 15px 0;
          line-height: 1.4;
        }

        .prediction-time {
          text-align: center;
          font-size: 0.9em;
          color: #ccc;
          margin-top: 15px;
        }

        .weather-details {
          margin: 20px 0;
          padding: 15px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 10px;
          backdrop-filter: blur(5px);
        }

        .weather-details h3 {
          text-align: center;
          margin-bottom: 15px;
          font-size: 1.1em;
          color: #fff;
        }

        .weather-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 10px;
        }

        .weather-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 12px;
          background: rgba(255, 255, 255, 0.15);
          border-radius: 8px;
          font-size: 0.9em;
        }

        .weather-item .label {
          color: #ccc;
          font-weight: 500;
        }

        .weather-item .value {
          color: #fff;
          font-weight: bold;
        }

        .error {
          color: #FF6B6B;
          text-align: center;
          font-size: 1.1em;
          font-weight: bold;
        }

        .error-details {
          color: #FFA500;
          text-align: center;
          font-size: 0.9em;
          margin-top: 10px;
        }

        @media (max-width: 600px) {
          .container {
            padding: 15px;
          }
          
          h1 {
            font-size: 2em;
          }
          
          .buttons {
            grid-template-columns: 1fr;
          }
          
          button {
            padding: 12px 20px;
            font-size: 14px;
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
          font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        #__next {
          height: 100%;
        }
      `}</style>
    </>
  );
} 