FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지 설치 (ML 라이브러리 컴파일용)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트 복사
COPY . .

# 기본 명령어
CMD ["python", "-c", "print('Weather ML Container Ready!')"]