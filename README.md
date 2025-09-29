# 프로젝트 이름

<br>

## 💻 프로젝트 소개
### <프로젝트 소개>
- **날씨 쾌적지수 예측 시스템**: 머신러닝을 활용한 날씨 데이터 기반 쾌적도 예측 서비스

### <작품 소개>
- **FastAPI + Streamlit**: 실시간 날씨 데이터를 입력받아 쾌적지수(0-10점)를 예측하는 웹 서비스
- **AWS S3 모델 저장소**: 최고 성능 모델을 S3에 저장하고 자동으로 로드
- **Docker 기반**: 완전한 컨테이너화된 MLOps 파이프라인

<br>

## 👨‍👩‍👦‍👦 팀 구성원

| ![박패캠](https://avatars.githubusercontent.com/u/156163982?v=4) | ![이패캠](https://avatars.githubusercontent.com/u/156163982?v=4) | ![최패캠](https://avatars.githubusercontent.com/u/156163982?v=4) | ![김패캠](https://avatars.githubusercontent.com/u/156163982?v=4) | ![오패캠](https://avatars.githubusercontent.com/u/156163982?v=4) |
| :--------------------------------------------------------------: | :--------------------------------------------------------------: | :--------------------------------------------------------------: | :--------------------------------------------------------------: | :--------------------------------------------------------------: |
|            [박패캠](https://github.com/UpstageAILab)             |            [이패캠](https://github.com/UpstageAILab)             |            [최패캠](https://github.com/UpstageAILab)             |            [김패캠](https://github.com/UpstageAILab)             |            [오패캠](https://github.com/UpstageAILab)             |
|                            팀장, 담당 역할                             |                            담당 역할                             |                            담당 역할                             |                            담당 역할                             |                            담당 역할                             |

<br>

## 🔨 개발 환경 및 기술 스택
- 주 언어 : _ex) python_
- 버전 및 이슈관리 : _ex) github_
- 협업 툴 : _ex) github, notion_

<br>

## 📁 프로젝트 구조
```
├── .github/                    # GitHub Actions 워크플로우
├── api/                        # FastAPI 애플리케이션
│   └── main.py                 # FastAPI 메인 앱
├── src/                        # 공통 소스 코드
│   ├── data/                   # 데이터 수집/전처리
│   ├── models/                 # ML 모델 학습/평가
│   │   ├── train.py           # 모델 학습 및 S3 저장
│   │   └── split.py           # 데이터 분할/전처리
│   └── utils/                  # 유틸리티 (S3 연동 등)
├── notebooks/                  # Jupyter 노트북
├── docs/                       # 문서
├── dockerfiles/                # Docker 설정 파일
├── app.py                      # Streamlit 웹 애플리케이션
├── docker-compose.yml          # 전체 시스템 구성
├── requirements.txt            # Python 패키지 의존성
└── README.md                   # 프로젝트 문서

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

## 📌 프로젝트 회고
### 박패캠
- _프로젝트 회고를 작성해주세요_

<br>

## 📰​ 참고자료
- _참고자료를 첨부해주세요_
