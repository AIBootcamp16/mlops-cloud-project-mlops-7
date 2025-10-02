
```markdown
# Weather API Server 배포 가이드

## 1. 사전 준비

### 1.1 필요한 정보 수집
- Batch 서버 Private IP: `172.31.7.11`
- DB 접속 정보 (팀원에게 받기):
  - DB_USER
  - DB_PASSWORD
  - DB_NAME

### 1.2 AWS CLI 설치 및 인증 설정
```bash
# AWS CLI 설치 (Ubuntu)
sudo apt update
sudo apt install awscli -y

# AWS 인증 설정
aws configure
# Access Key, Secret Key, Region(ap-northeast-2) 입력
```

## 2. 환경변수 설정

```bash
# 작업 디렉토리 생성
mkdir -p ~/weather-api
cd ~/weather-api

# .env 파일 생성
nano .env
```

```shellscript
# .env 내용
DB_HOST=172.31.7.11
DB_PORT=3306
DB_USER=weather_user
DB_PASSWORD=팀원에게_받은_패스워드
DB_NAME=weather_mlops
```

## 3. docker-compose.yml 생성

```bash
nano docker-compose.yml
```

```yaml
services:
  api:
    image: 152864141231.dkr.ecr.ap-northeast-2.amazonaws.com/weather-api:latest
    ports:
      - "8000:8000"
    environment:
      - DB_HOST=${DB_HOST}
      - DB_PORT=${DB_PORT}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_NAME=${DB_NAME}
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

## 4. Docker 설치

```bash
# Docker 설치
sudo apt update
sudo apt install -y docker.io docker-compose

# Docker 권한 설정
sudo usermod -aG docker $USER
newgrp docker

# Docker 서비스 시작
sudo systemctl start docker
sudo systemctl enable docker
```

## 5. ECR에서 이미지 Pull

```bash
# ECR 로그인
aws ecr get-login-password --region ap-northeast-2 | \
docker login --username AWS --password-stdin \
152864141231.dkr.ecr.ap-northeast-2.amazonaws.com

# 이미지 pull
docker-compose pull
```

## 6. 컨테이너 실행

```bash
# 컨테이너 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f api
```

## 7. 헬스체크 및 테스트

```bash
# API 서버 헬스체크
curl http://localhost:8000/health

# 예상 응답: {"status": "healthy"}
```

## 8. 보안 그룹 설정

AWS 콘솔에서 API 서버 인스턴스의 보안 그룹 설정:

```
인바운드 규칙 추가:
- 유형: 사용자 지정 TCP
- 포트: 8000
- 소스: 0.0.0.0/0 (또는 특정 IP만 허용)
- 설명: API Server
```

## 9. 트러블슈팅

### 컨테이너가 시작되지 않는 경우
```bash
# 로그 확인
docker-compose logs api

# 컨테이너 재시작
docker-compose restart api
```

### DB 연결 실패
```bash
# DB 접속 테스트
telnet 172.31.7.11 3306

# MySQL 직접 연결 테스트 (mysql-client 설치 필요)
sudo apt install mysql-client -y
mysql -h 172.31.7.11 -u weather_user -p
```

### 이미지 pull 실패
```bash
# ECR 로그인 재시도
aws ecr get-login-password --region ap-northeast-2 | \
docker login --username AWS --password-stdin \
152864141231.dkr.ecr.ap-northeast-2.amazonaws.com

# 이미지 강제 pull
docker-compose pull --ignore-pull-failures
```

## 10. 업데이트 배포

빌드 서버에서 새 이미지를 푸시한 후:

```bash
# 최신 이미지 pull
docker-compose pull

# 컨테이너 재시작
docker-compose up -d

# 로그 확인
docker-compose logs -f api
```

## 11. 모니터링

```bash
# 실시간 로그 확인
docker-compose logs -f api

# 컨테이너 상태 확인
docker-compose ps

# 리소스 사용량 확인
docker stats
```

## 12. 컨테이너 중지/삭제

```bash
# 컨테이너 중지
docker-compose stop

# 컨테이너 삭제
docker-compose down

# 이미지까지 삭제
docker-compose down --rmi all
```

## 참고사항

- API 서버 포트: 8000
- DB는 Batch 서버(172.31.7.11)에서 실행 중
- 환경변수 변경 시 컨테이너 재시작 필요: `docker-compose up -d`
- 보안을 위해 .env 파일 권한 설정: `chmod 600 .env`
- 빌드는 별도 빌드 서버에서 수행, API 서버는 이미지만 pull
```

