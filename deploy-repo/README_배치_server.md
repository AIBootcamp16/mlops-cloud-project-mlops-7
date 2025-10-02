좋습니다 👍 그럼 제가 위에서 만든 마크다운을 **README.md 스타일**로 바로 쓸 수 있게 조금 더 다듬어드릴게요.
GitHub에서 보기 좋게 이모지·헤더 크기 조정·코드 블록 정리까지 반영했어요.

---

# Weather MLOps Batch 서버 배포 가이드

## 📋 목차

* [사전 준비](#-사전-준비)
* [배포 절차](#-배포-절차)
* [Airflow UI 접속](#-airflow-ui-접속)
* [DAG 활성화](#-dag-활성화)
* [유용한 명령어](#-유용한-명령어)
* [문제 해결](#-문제-해결)
* [업데이트 절차](#-업데이트-절차)
* [주의사항](#️-주의사항)
* [모니터링](#-모니터링)
* [연락처](#-연락처)

---

## ⚙️ 사전 준비

### 1. Docker 설치

```bash
# 시스템 업데이트
sudo apt update

# Docker 설치
sudo apt install -y docker.io docker-compose

# 현재 사용자를 docker 그룹에 추가
sudo usermod -aG docker ubuntu

# 로그아웃 후 재접속 (권한 적용)
exit
```

재접속 후 설치 확인:

```bash
docker --version
docker-compose --version
```

### 2. AWS CLI 설치

```bash
# AWS CLI v2 다운로드
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"

# unzip 설치
sudo apt install unzip -y

# 압축 해제 및 설치
unzip awscliv2.zip
sudo ./aws/install

# 설치 확인
aws --version
```

### 3. AWS 인증 설정

```bash
aws configure
```

입력 사항:

* **AWS Access Key ID**: [IAM에서 발급받은 키]
* **AWS Secret Access Key**: [IAM에서 발급받은 시크릿]
* **Default region name**: `ap-northeast-2`
* **Default output format**: `json`

---

## 🚀 배포 절차

### 1. 작업 디렉토리 생성

```bash
mkdir -p ~/weather-batch
cd ~/weather-batch
```

### .env.example 다운로드
curl -o .env.example \
  https://raw.githubusercontent.com/your-username/MLOPS-CLOUD-PROJECT-MLOPS-7/main2/deploy-repo/.env.example

### README.md
curl -o README.md \
  https://raw.githubusercontent.com/your-username/MLOPS-CLOUD-PROJECT-MLOPS-7/main/deploy-repo/README.md

### docker-compose.airflow.yml
curl -o docker-compose.airflow.yml \
  https://raw.githubusercontent.com/your-username/MLOPS-CLOUD-PROJECT-MLOPS-7/main/deploy-repo/docker-compose.airflow.yml
  

### 3. 환경변수 파일 생성

```bash
vim .env
```

`.env` 파일 예시:

```properties
# AWS S3
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=ap-northeast-2
S3_BUCKET=weather-mlops-team-data

# 챔피언 모델
CHAMPION_MODEL=champion/rf-weather-predictor-019

# MySQL
MYSQL_HOST=mysql
MYSQL_USER=root
MYSQL_ROOT_PASSWORD=your_password
MYSQL_DATABASE=weather_mlops

# WandB
WANDB_API_KEY=your_wandb_key
WANDB_ENTITY=your_entity
WANDB_PROJECT=weather-predictor
WANDB_MODE=online
```

### 4. ECR 로그인

```bash
aws ecr get-login-password --region ap-northeast-2 | \
  docker login --username AWS --password-stdin \
  1528641412.dkr.ecr.ap-northeast-2.amazonaws.com
```

성공 시: `Login Succeeded`

### 5. 이미지 Pull

```bash
docker-compose -f docker-compose.airflow.yml pull
```

### 6. 컨테이너 실행

```bash
docker-compose -f docker-compose.airflow.yml up -d
```

### 7. 로그 확인

```bash
# 전체 로그
docker-compose -f docker-compose.airflow.yml logs -f

# 특정 서비스 로그
docker-compose -f docker-compose.airflow.yml logs -f airflow-scheduler
```

---

## 🌐 Airflow UI 접속

브라우저 접속:

```
http://[서버-공인-IP]:8080
```

로그인 정보:

* Username: `admin`
* Password: `admin`

---

## ▶️ DAG 활성화

1. Airflow UI 접속
2. 왼쪽 메뉴에서 **`batch_inference_pipeline`** DAG 선택
3. 토글 스위치를 **ON**으로 변경

자동 실행: 매시간 5분 (`00:05, 01:05, 02:05, ...`)

---

## 🛠 유용한 명령어

컨테이너 상태 확인

```bash
docker-compose -f docker-compose.airflow.yml ps
```

컨테이너 재시작

```bash
docker-compose -f docker-compose.airflow.yml restart
```

컨테이너 중지

```bash
docker-compose -f docker-compose.airflow.yml down
```

컨테이너 중지 + 볼륨 삭제

```bash
docker-compose -f docker-compose.airflow.yml down -v
```

MySQL 접속

```bash
docker-compose -f docker-compose.airflow.yml exec mysql mysql -u root -p
```

디스크 사용량 확인

```bash
df -h
docker system df
```

---

## ❗ 문제 해결

### 포트 충돌 (8080)

```bash
sudo lsof -i :8080
sudo kill -9 [PID]
```

### 디스크 공간 부족

```bash
docker image prune -a
docker volume prune
docker system prune -a --volumes   # 전체 정리 (주의!)
```

### 권한 오류

```bash
sudo chown -R ubuntu:ubuntu ~/weather-batch
chmod 600 ~/weather-batch/.env
```

### 컨테이너 실행 오류

```bash
docker-compose -f docker-compose.airflow.yml logs
docker-compose -f docker-compose.airflow.yml logs airflow-init
```

---

## 🔄 업데이트 절차

새 이미지 배포 시:

```bash
cd ~/weather-batch

# 1. ECR 로그인
aws ecr get-login-password --region ap-northeast-2 | \
  docker login --username AWS --password-stdin \
  1528641412.dkr.ecr.ap-northeast-2.amazonaws.com

# 2. 최신 이미지 pull
docker-compose -f docker-compose.airflow.yml pull

# 3. 컨테이너 재시작
docker-compose -f docker-compose.airflow.yml up -d

# 4. 로그 확인
docker-compose -f docker-compose.airflow.yml logs -f
```

---

## ⚠️ 주의사항

* `.env` 파일은 민감 정보 포함 → **`chmod 600 .env`** 필수
* ECR 로그인 토큰은 **12시간 유효**, 만료 시 재로그인 필요
* MySQL 데이터는 **mysql_data 볼륨**에 영구 저장
* 서버 재부팅 시 컨테이너 자동 시작 (`restart: unless-stopped`)

---

## 📊 모니터링

컨테이너 리소스 확인

```bash
docker stats
```

DAG 실행 이력 확인:
**Airflow UI → Browse → DAG Runs**

---

## 📞 연락처

문제 발생 시: [hyoentae@naver.com]

---


