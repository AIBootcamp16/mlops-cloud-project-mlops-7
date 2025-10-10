# 프로젝트 이름

<br>

## 💻 프로젝트 소개
### <프로젝트 소개>
<<<<<<< HEAD

- **날씨 쾌적지수 예측 시스템**: 머신러닝을 활용한 날씨 데이터 기반 쾌적도 예측 서비스

### <작품 소개>
- **FastAPI + Streamlit**: 실시간 날씨 데이터를 입력받아 쾌적지수를 예측하는 웹 서비스
- **AWS S3 모델 저장소**: 최고 성능 모델을 S3에 저장하고 자동으로 로드

=======


### <작품 소개>
- 기상청 앱의 일반적인 날씨 정보를 넘어, 출퇴근 시간대에 특화된 쾌적지수를 제공하여 도보·자전거 이용자 등 날씨에 민감한 직장인들이 출근 준비나 퇴근 후 약속 계획을 보다 효율적으로 세울 수 있도록 돕고자 한다. 

<br>

## 👨‍👩‍👦‍👦 팀 구성원

### 안현태 (팀장): 
구조 및 배포 설계/데이터 파이프라인 관리 
### 문서연: 
아이디어 제공 (주제선정, 프론트화면)/데이터 적재 및 피처 담당 
### 손은혜: 
프론트엔드 구현 및 배포/백엔드 구현 및 FastAPI /모델 학습 및 추론 (WANDB 연동) 
### 정용재: 
Orchestrated experiment 와 배치 추론 단계에서 AirflowDAG 구현 수행
### 주예령: 
EDA


<br>

## 🔨 개발 환경 및 기술 스택
- 주 언어 :  python, java
- 버전 및 이슈관리 : github
- 협업 툴 : github, notion

<br>

## 📁 프로젝트 구조
```
├── Airflow                     # DAG 관련 
├── api/                        # FastAPI 애플리케이션
│   ├── main.py                 # FastAPI 메인 앱
│   └── Dockerfile              # FastAPI Dockerfile
├── src/                        # 공통 소스 코드
│   ├── data/                   # 데이터 관련 패키지
│   ├── models/                 # ML 모델 학습 및 평가 관련 패키지
│   └── utils/                  # 유틸리티 패키지
│   └── storage/                # s3 관련 
├── .env.example                # 환경 변수 예시
├── .dockerignore               # Docker ignore 파일
├── .gitignore                  # Git ignore 파일
├── docker-compose.yml          # Docker Compose file
├── pyproject.toml              # 메인 Poetry 설정
└── README.md                   # 프로젝트 README
<<<<<<< HEAD
>>>>>>> origin/main2
=======
>>>>>>> origin/main2

```

<br>
# 1. main 브랜치로 전환
git checkout main
git pull

# 2. 프로덕션 이미지 빌드 (소스코드 포함)
docker build \
  --target collector \
  -t weather-collector:v1.0.0 \
  -f Dockerfile.multi .

# 3. 테스트
docker run --env-file .env weather-collector:v1.0.0

# 4. 이미지 레지스트리에 푸시
docker tag weather-collector:v1.0.0 your-registry/weather-collector:v1.0.0
docker push your-registry/weather-collector:v1.0.0
<br>

<br>

## 💻​ 구현 기능
### 데이터 수집 및 전처리
### 쾌적지수 예측 모델 개발
### MLOps 파이프라인 구축
### FastAPI 및 프론트엔드 개발
### Vercel에 배포
<br>


<br>

## 🚨​ 트러블 슈팅
### 1. 단기예보 데이터가 모델이 학습한 실시간 데이터 구조와 달라 단기예보를 바탕으로 쾌적지수를 예측 할 수 없었다.

#### 해결
-  이 문제는 출퇴근 쾌적 지수를 볼 때는 시간 제약을 둬 마치 예측하는 것처럼 보이게 하는 것으로 해결했다.

<br>

<<<<<<< HEAD

## 🚀 실행 방법

### 1. 환경 설정
```bash
# .env 파일 생성 (AWS 자격증명 필요)
cp .env.example .env
# .env 파일에 AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET 등 설정
```

### 2. Docker Compose로 전체 시스템 실행
```bash
# 전체 서비스 실행
docker-compose up

# 개별 서비스 실행

| 서비스 | 포트 | 접속 URL | 상태 |
|--------|------|----------|------|
| **Frontend (Next.js)** | 3000 | `http://localhost:3000` | ✅ Up |
| **FastAPI** | 8000 | `http://localhost:8000` | ✅ Up |
| **MySQL** | 3307 | `localhost:3307` | ✅ Up |
| **phpMyAdmin** | 8081 | `http://localhost:8081` | ✅ Up |


### 4. 모델 학습 (선택사항)
```bash
# 컨테이너 내에서 모델 학습
docker-compose exec api-server python src/models/train.py
```



<br>

## 📰​ 참고자료
- 기상청 종합기상정보(KMA) 공개 API
