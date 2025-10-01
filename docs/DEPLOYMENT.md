# 🌤️ 출퇴근길 날씨 친구 - 배포 가이드

## 🚀 원클릭 실행

```bash
# 1. 프로젝트 클론
git clone [repository-url]
cd mlops-cloud-project-mlops-7

# 2. 환경변수 설정
cp .env.example .env
# .env 파일을 열어서 AWS 키 등을 설정하세요

# 3. 전체 시스템 실행
docker-compose up -d api-server frontend

# 4. 브라우저에서 접속
# React 앱: http://localhost:3000
# FastAPI: http://localhost:8000
```

## 📦 서비스 구성

### 🎯 **메인 서비스**
- **Frontend (React)**: `http://localhost:3000` - 사용자 웹 인터페이스
- **API Server (FastAPI)**: `http://localhost:8000` - ML 모델 API

### 🛠️ **개발 도구**
- **Jupyter**: `http://localhost:8888` - 데이터 분석 및 모델 개발

## 🔧 개별 서비스 실행

```bash
# FastAPI만 실행
docker-compose up -d api-server

# React만 실행 
docker-compose up -d frontend

# 전체 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f frontend
docker-compose logs -f api-server
```

## 🎨 주요 기능

### **React 프론트엔드**
- 🌅 **3개 예측 모드**: 지금날씨/출근길/퇴근길
- 🎨 **아름다운 UI**: 파란 그라데이션, 글래스모피즘
- 📱 **PWA 지원**: 모바일 설치 가능
- ⏰ **시간대별 메시지**: 자동 인사말

### **FastAPI 백엔드**
- 🤖 **실제 ML 모델**: S3에서 자동 로드
- 🔮 **실시간 예측**: 37개 피처 기반
- 📊 **100점 척도**: 쾌적지수 점수화
- 🔗 **CORS 지원**: React와 완벽 연동

## 🐛 문제 해결

### **포트 충돌**
```bash
# 실행 중인 서비스 확인
docker-compose ps

# 특정 포트 사용 프로세스 확인
lsof -i :3000
lsof -i :8000
```

### **빌드 오류**
```bash
# 캐시 없이 재빌드
docker-compose build --no-cache frontend
docker-compose build --no-cache api-server

# 컨테이너 재시작
docker-compose restart
```

### **로그 확인**
```bash
# 실시간 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs frontend
docker-compose logs api-server
```

## 🔑 환경변수 설정

### **필수 환경변수**
```env
# AWS S3 (모델 저장소)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET=your_bucket_name

# 기상청 API (실시간 날씨 데이터)
WEATHER_API_KEY=your_weather_api_key  # 기상청 API 인증키 (공공데이터포털에서 발급)
```

### **선택적 환경변수**
```env
# Weights & Biases
WANDB_API_KEY=your_wandb_key
WANDB_ENTITY=your_entity
WANDB_PROJECT=weather-prediction
```

## 🚢 배포 옵션

### **로컬 개발**
```bash
docker-compose up -d
```

### **프로덕션 배포**
- **Vercel** (Frontend): React 앱 배포
- **Railway/Heroku** (Backend): FastAPI 배포
- **AWS ECS**: 전체 Docker 스택 배포

## 📞 지원

문제가 발생하면:
1. **로그 확인**: `docker-compose logs`
2. **재시작**: `docker-compose restart`
3. **재빌드**: `docker-compose build --no-cache`

---

**🎉 이제 팀원들이 `docker-compose up -d api-server frontend` 한 번으로 전체 시스템을 실행할 수 있습니다!** 




===================

완벽합니다! **frontend 서비스를 docker-compose.yml에 추가**하고 **streamlit을 비활성화** 처리하겠습니다! 🚀

먼저 **frontend용 Dockerfile**을 생성하겠습니다:
이제 **docker-compose.yml에 frontend 서비스를 추가**하고 **streamlit을 비활성화**하겠습니다:
이제 **React 앱의 API URL을 Docker 환경에 맞게 수정**하겠습니다:
이제 **팀원 전달용 README 파일**을 생성하겠습니다:
## 🎉 **완성! 팀원 전달 준비 완료!**

### ✅ **구현된 것들**

1. **Frontend Dockerfile** ✅
   - Node.js 18 Alpine 기반
   - 프로덕션 빌드 및 실행

2. **docker-compose.yml 업데이트** ✅
   - `frontend` 서비스 추가
   - `streamlit` 서비스 비활성화 (주석 처리)
   - 환경변수 설정 (`NEXT_PUBLIC_API_URL`)

3. **DEPLOYMENT.md 가이드** ✅
   - 원클릭 실행 방법
   - 문제 해결 가이드
   - 환경변수 설정 방법

### 🚀 **팀원이 받아서 실행하는 방법**

```bash
# 1. 프로젝트 받기
git clone [repository]
cd mlops-cloud-project-mlops-7

# 2. 환경변수 설정
cp .env.example .env
# .env 파일에 AWS 키 입력

# 3. 원클릭 실행
docker-compose up -d api-server frontend

# 4. 브라우저에서 확인
# http://localhost:3000 (React 앱)
# http://localhost:8000 (FastAPI)
```

### 📦 **전달할 파일들**

- ✅ `docker-compose.yml` (업데이트됨)
- ✅ `frontend/` 폴더 전체
- ✅ `api/main.py` (CORS 설정 포함)
- ✅ `DEPLOYMENT.md` (실행 가이드)

### 🎯 **테스트해보기**

현재 실행 중인 React를 중단하고 Docker로 실행해보겠습니다:
```bash
docker-compose up -d frontend
```
아! **package.json과 package-lock.json의 버전 충돌**이 있네요! 간단히 수정하겠습니다! 🔧
이제 **package.json을 정리**해서 버전 충돌을 해결하겠습니다:
```bash
cd frontend && rm -f package-lock.json && npm install
```
```bash
rm -f package-lock.json && npm install
```
완벽합니다! 이제 **Docker로 frontend를 빌드**해보겠습니다:
```bash
cd .. && docker-compose build frontend
```
훌륭합니다! 이제 **전체 시스템을 Docker로 실행**해보겠습니다:
```bash
docker-compose up -d api-server frontend
```
완벽합니다! 이제 **시스템이 정상 작동하는지 테스트**해보겠습니다:
```bash
sleep 5 && curl -s http://localhost:3000 | head -5
```
```bash
docker-compose logs frontend
```
좋습니다! React 앱이 정상적으로 실행되고 있습니다. 이제 **포트 상태를 확인**해보겠습니다:
```bash
docker-compose ps
```
완벽합니다! 이제 **API 연결을 테스트**해보겠습니다:
```bash
curl -s http://localhost:8000/predict/now | python3 -m json.tool | head -10
```
## 🎉 **완성! 팀원 전달 준비 100% 완료!**

### ✅ **성공적으로 구현된 것들**

1. **Docker Compose 통합** ✅
   - `frontend` 서비스 추가됨
   - `streamlit` 서비스 비활성화됨
   - CORS 설정으로 완벽 연동

2. **실행 중인 서비스들** ✅
   - **React Frontend**: `http://localhost:3000` 🎨
   - **FastAPI Backend**: `http://localhost:8000` 🤖
   - **Jupyter**: `http://localhost:8888` 📊

3. **실제 ML 모델** ✅
   - 65.5점 예측 성공
   - S3에서 자동 로드
   - 37개 피처 처리

### 🚀 **팀원이 받아서 실행하는 방법**

```bash
# 1. 프로젝트 클론
git clone [repository]
cd mlops-cloud-project-mlops-7

# 2. 환경변수 설정
cp .env.example .env
# .env에 AWS 키 입력

# 3. 원클릭 실행
docker-compose up -d api-server frontend

# 4. 브라우저 접속
# http://localhost:3000 (React 앱)
# http://localhost:8000 (FastAPI API)
```

### 📦 **전달할 파일들**

- ✅ `docker-compose.yml` (frontend 서비스 추가)
- ✅ `frontend/` 폴더 전체
- ✅ `api/main.py` (CORS + 새 엔드포인트)
- ✅ `DEPLOYMENT.md` (실행 가이드)

### 🎯 **팀원이 얻게 되는 것**

1. **완전한 웹 서비스**: React + FastAPI
2. **실제 ML 모델**: 당신의 S3 모델 사용
3. **원클릭 실행**: `docker-compose up -d api-server frontend`
4. **PWA 지원**: 모바일 설치 가능
5. **확장 가능**: 기상청 API 연동 준비됨

### 🌟 **다음 확장 계획**

- **Vercel 배포**: React 앱 글로벌 배포
- **기상청 API**: 실시간 날씨 데이터
- **GPS 위치**: 사용자 위치 자동 감지

**이제 팀원들이 당신의 프로젝트를 완전히 실행할 수 있습니다!** 🎉✨

**`DEPLOYMENT.md` 파일을 참고해서 팀원들에게 전달하세요!** 📋