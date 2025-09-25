
├── api/                            # FastAPI 애플리케이션
│   └── Dockerfile                  # FastAPI 메인 앱
│   
├── dockerfiles
│   ├── Dockerfile                  # 운영용 dockerfile
│   └── Dockerfile.jupyter          # 개발용 dockerfile.jupyter
│
├── models
│
├── src/                            # 공통 소스 코드
│   ├── data/                       # 데이터 관련 패키지
│   │     ├── crawler.py            # 크롤링 후 s3 적재
│   │     ├── s3_call.py         # s3 호출 
│   │     ├── data_cleaning.py   # 데이터 정제 (필요한 특성만 가져온 뒤 train-val-test 분리 후 결측치, 이상치 처리 및 파생변수 생성)
│   │     └── preprocessing.py   # 전처리 (표준화, 정규화, 인코딩)
│   │     
│   ├── models/                     # ML 모델 학습 및 평가 관련 패키지
│   │        ├── split.py           # train-val-test 분리 
│   │        ├── models.py          # 모델 불러오기 (get_model) 
│   │        └── train.py           # 모델 학습 (get_model() 학습, WANDB저장)
│   │
│   └── utils/                      # 유틸리티 패키지
│
├── tests/                          # 테스트
├── notebooks/                      # Jupyter 노트북
│   ├── fonts/                      # ttf 파일 모음 directory
│   └── notebook_template.ipynb     # Jupyter Notebook Template
├── docs/                           # 문서
├── .env.example                    # 환경 변수 예시
├── .dockerignore                   # Docker ignore 파일
├── .gitignore                      # Git ignore 파일
├── docker-compose.yml              # Docker Compose file
├── pyproject.toml                  # 메인 Poetry 설정
└── README.md                       # 프로젝트 README




기상청 데이터 크롤링 -> s3 적재 -> s3 호출 -> 데이터 정재 -> 데이터 전처리 -> 모델 학습 -> 모델 평가 -> 배포

if "__name__" == __main__:

    df.drop("tm",axis=1).inplace=True
    df = drop(df)

    trian, val, test =train_val_test(df)

    train, val, test =cleaning(train, val, test)

     

   
