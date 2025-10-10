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
- _이번 프로젝트에 대해 소개를 작성해주세요_

### <작품 소개>
- _만드신 작품에 대해 간단한 소개를 작성해주세요_
>>>>>>> origin/main2

<br>

## 👨‍👩‍👦‍👦 팀 구성원

안현태 (팀장): 구조 및 배포 설계/데이터 파이프라인 관리
문서연: 아이디어 제공 (주제선정, 프론트화면)/데이터 적재 및 피처 담당 
손은혜: 프론트엔드 구현 및 배포/백엔드 구현 및 FastAPI /모델 학습 및 추론 (WANDB 연동) 
정용재: Orchestrated experiment 와 배치 추론 단계에서 AirflowDAG 구현 수행
주예령: EDA


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
### 기능1
- _작품에 대한 주요 기능을 작성해주세요_
### 기능2
- _작품에 대한 주요 기능을 작성해주세요_
### 기능3
- _작품에 대한 주요 기능을 작성해주세요_

<br>

## 🛠️ 작품 아키텍처(필수X)
- #### _아래 이미지는 예시입니다_
![이미지 설명](https://miro.medium.com/v2/resize:fit:4800/format:webp/1*ub_u88a4MB5Uj-9Eb60VNA.jpeg)

<br>

## 🚨​ 트러블 슈팅
### 1. OOO 에러 발견

#### 설명
- _프로젝트 진행 중 발생한 트러블에 대해 작성해주세요_

#### 해결
- _프로젝트 진행 중 발생한 트러블 해결방법 대해 작성해주세요_

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
docker-compose up api-server    # FastAPI 서버 (포트: 8000)
docker-compose up streamlit     # Streamlit 웹앱 (포트: 8501)
```

### 3. 서비스 접속
- **Streamlit 웹앱**: http://localhost:8501
- **FastAPI 문서**: http://localhost:8000/docs
- **API 상태 확인**: http://localhost:8000/health

### 4. 모델 학습 (선택사항)
```bash
# 컨테이너 내에서 모델 학습
docker-compose exec api-server python src/models/train.py
```


=======
>>>>>>> origin/main2
## 📌 프로젝트 회고
### 박패캠
- _프로젝트 회고를 작성해주세요_

<br>

## 📰​ 참고자료
- _참고자료를 첨부해주세요_
