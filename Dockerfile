# 운영용 Dockerfile
FROM python:3.11-bookworm

# 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Seoul \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/src

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential gcc tzdata curl \
      fonts-noto-cjk fonts-noto-cjk-extra \
 && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
 && echo $TZ > /etc/timezone \
 && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    pip install -r requirements.txt

# 애플리케이션 소스 코드 복사
COPY src/ ./src/

# 필요한 디렉토리 생성
RUN mkdir -p data logs models experiments

# 비root 사용자 생성 (보안)
RUN groupadd -r mlops && useradd -r -g mlops mlops
RUN chown -R mlops:mlops /app
USER mlops

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# 기본 명령어 (유연하게 오버라이드 가능)
CMD ["python", "-c", "print('MLOps Container Ready')"]