# 프로젝트 이름

<br>

## 💻 프로젝트 소개
### <프로젝트 소개>
- _이번 프로젝트에 대해 소개를 작성해주세요_

### <작품 소개>
- _만드신 작품에 대해 간단한 소개를 작성해주세요_

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
│   └── workflows/
├── api/                        # FastAPI 애플리케이션
│   ├── main.py                 # FastAPI 메인 앱
│   └── Dockerfile              # FastAPI Dockerfile
├── src/                        # 공통 소스 코드
│   ├── data/                   # 데이터 관련 패키지
│   ├── models/                 # ML 모델 학습 및 평가 관련 패키지
│   └── utils/                  # 유틸리티 패키지
├── tests/                      # 테스트
├── notebooks/                  # Jupyter 노트북
│   ├── fonts/                  # ttf 파일 모음 directory
│   └── notebook_template.ipynb # Jupyter Notebook Template
├── docs/                       # 문서
├── .env.example                # 환경 변수 예시
├── .dockerignore               # Docker ignore 파일
├── .gitignore                  # Git ignore 파일
├── docker-compose.yml          # Docker Compose file
├── pyproject.toml              # 메인 Poetry 설정
└── README.md                   # 프로젝트 README

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

## 📌 프로젝트 회고
### 박패캠
- _프로젝트 회고를 작성해주세요_

<br>

## 📰​ 참고자료
- _참고자료를 첨부해주세요_
