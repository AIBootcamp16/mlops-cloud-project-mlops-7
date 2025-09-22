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
weather-mlops/
├─ data/                          # 데이터 저장소
│  ├─ raw/                        # API 원천 데이터 그대로
│  ├─ interim/                    # 정제/전처리된 중간 데이터
│  └─ processed/                  # 최종 피처/지수 결과 테이블
│
├─ src/                           # 실제 코드
│  ├─ data/                       # 데이터 수집 및 전처리
│  │   ├─ kma_client.py           # 기상청 API 호출 (ASOS/UV/PM 등)
│  │   ├─ fetch.py                # 여러 API 모듈 통합 호출
│  │   └─ preprocess.py           # 결측/타입 정리, 구간화 전 준비
│  │
│  ├─ features/                   # 피처 엔지니어링
│  │   ├─ penalty_rules.py        # 항목별 벌점(HeatPenalty, UVPenalty 등)
│  │   └─ feature_builder.py      # 모든 피처/벌점 합쳐 DataFrame 생성
│  │
│  ├─ indices/                    # 지수 계산 로직
│  │   ├─ comfort_index.py        # 불쾌지수 → 쾌적지수 계산 함수
│  │   └─ weights.yaml            # 가중치 설정(Heat=0.45, UV=0.20 등)
│  │
│  ├─ serving/                    # 서비스/배포
│  │   └─ app.py                  # FastAPI 엔드포인트 (/predict)
│  │
│  └─ utils/                      # 공용 유틸
│      ├─ io.py                   # 데이터 저장/불러오기 (Parquet, CSV 등)
│      ├─ config.py               # 설정 로더(pydantic/yaml)
│      └─ logger.py               # 로깅 공통
│
├─ conf/
│  └─ config.yaml                 # API 키, 스테이션ID, 경로 등 공용 설정
│
├─ tests/                         # 테스트
│  ├─ test_penalty_rules.py       # 구간화/벌점 함수 단위 테스트
│  ├─ test_comfort_index.py       # 최종 지수 계산 검증
│  └─ test_api.py                 # FastAPI 응답 검증
│
├─ notebooks/                     # EDA 및 실험용
│  ├─ eda.ipynb                   # 데이터 탐색
│  └─ index_experiment.ipynb      # 가중치 실험/시각화
│
├─ .env.example                   # 예시 환경변수(KMA_API_KEY=...)
├─ requirements.txt               # 의존성
├─ README.md                      # 프로젝트 설명/실행법
├─ Makefile                       # 자주 쓰는 명령어 단축 (fetch, build, serve 등) 너가 짜준 디렉토리 구조는 이거야 여기에 맞는 도커 파일 짜줘
├─ .gitignore                     
├─ Dockerfile                     # 배포용
├─ Dockerfile.dev                 # 개발용
│
└─ .github
    └─ISSUE_TEMPLATE              # ISSYE 템플릿 작성 예시
       ├─ bug-data.yml            # 데이터 수집/정합성
       ├─ bug-feature.yml         # 피처 로직
       ├─ bug-infra.yml           # 학습 평가
       ├─ bug-pipeline.yml        # 서빙/API
       ├─ bug-serve.yml           # Airflow/오케스트레이션
       ├─ bug-train.yml           # CI/CD/도커/권한
       └─ bug.yml                 # 기본 

```

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
