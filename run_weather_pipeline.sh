#!/bin/bash

echo "======================================"
echo "🌦️  기상 데이터 수집 및 S3 적재 실험"
echo "======================================"

# 환경 변수 확인
if [ ! -f .env ]; then
    echo "❌ .env 파일이 없습니다!"
    echo "📝 .env.example을 복사해서 .env 파일을 만들고 API 키를 설정하세요."
    exit 1
fi

echo ""
echo "1️⃣ 환경 변수 로드 중..."
source .env

echo "2️⃣ Python 스크립트 실행 중..."
python3 src/data/weather_processor.py

echo ""
echo "✅ 실험 완료!"
