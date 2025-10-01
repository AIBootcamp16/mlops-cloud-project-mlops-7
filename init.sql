CREATE TABLE IF NOT EXISTS weather_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- 예측 결과
    comfort_score FLOAT NOT NULL,
    
    -- 기상 데이터
    temperature FLOAT,
    humidity FLOAT,
    rainfall FLOAT,
    pm10 FLOAT,
    wind_speed FLOAT,
    pressure FLOAT,
    
    -- 시간 정보
    prediction_datetime DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 지역 정보
    region VARCHAR(50),
    station_id VARCHAR(20),
    
    -- 모델 정보
    model_name VARCHAR(100),
    
    -- UNIQUE 제약: 같은 시간대는 1개만
    UNIQUE KEY uk_prediction (prediction_datetime, station_id),
    
    INDEX idx_prediction_datetime (prediction_datetime DESC),
    INDEX idx_region (region)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4; 