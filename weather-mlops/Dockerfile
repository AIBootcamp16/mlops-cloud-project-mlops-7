# weather-mlops/Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Seoul \
    PIP_NO_CACHE_DIR=1

# OS 필수 패키지
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential gcc tzdata curl \
 && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
 && echo $TZ > /etc/timezone \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1) requirements만 먼저 복사 → 의존성 캐시
COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    pip install -r requirements.txt

# 2) 애플리케이션 소스/설정 복사 (merge된 코드가 들어감)
COPY src/ src/
COPY conf/ conf/
COPY .env.example .env.example
COPY README.md .

# 비루트 실행(보안)
RUN useradd -m appuser
USER appuser

# 기본 실행: FastAPI 서버 (필요 시 docker run에서 명령으로 override 가능)
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "src.serving.app:app", "--host", "0.0.0.0", "--port", "8000"]
