# 모델 실험

참고: 001/002 는 자동 번호 생성 테스트 했음. 003부터. 

## 1. 현 코드로 다음 명령어로 돌려봄. 

실험명: weather-predictor-003
모델: 전체 7개 모델 (linear, ridge, lasso, rf, lgbm, xgb, cat)
WANDB: realtheai-insight-/weather-predictor 프로젝트에 003번으로 기록
S3: s3://weather-mlops-team-data/models/weather-predictor-003/에 최고 모델 저장

```
docker exec -it mlops-cloud-project-mlops-7-jupyter-1 bash -c "python /app/src/models/train.py"
```
### 결과

```
시드 42로 고정 완료
wandb: Currently logged in as: realtheai-insight (realtheai-insight-). Use `wandb login --relogin` to force relogin
wandb: wandb version 0.22.0 is available!  To upgrade, please run:
wandb:  $ pip install wandb --upgrade
wandb: Tracking run with wandb version 0.16.3
wandb: Run data is saved locally in /app/wandb/run-20250928_064947-dikoytfx
wandb: Run `wandb offline` to turn off syncing.
wandb: Syncing run weather-predictor-003
wandb: ⭐️ View project at https://wandb.ai/realtheai-insight-/weather-predictor
wandb: 🚀 View run at https://wandb.ai/realtheai-insight-/weather-predictor/runs/dikoytfx
🚀 모델 학습 시작...
🔄 S3에서 데이터 로드 중...
시드 42로 고정 완료
데이터 로드 완료: (342500, 34)
결측치 많은 컬럼 제거: ['rainfall']
원핫인코딩 적용: ['season', 'temp_category', 'pm10_grade', 'region']
피처: 29개, 샘플: 342500개
Train: (205500, 37), Val: (68500, 37), Test: (68500, 37)
✅ 데이터 분할 및 스케일링 완료

📊 LINEAR 모델 학습 중...
✅ linear: Val RMSE=3.6223, Test RMSE=3.6396

📊 RIDGE 모델 학습 중...
✅ ridge: Val RMSE=3.6223, Test RMSE=3.6396

📊 LASSO 모델 학습 중...
✅ lasso: Val RMSE=4.5277, Test RMSE=4.5455

📊 RF 모델 학습 중...
✅ rf: Val RMSE=2.5421, Test RMSE=2.5306

📊 LGBM 모델 학습 중...
✅ lgbm: Val RMSE=3.1257, Test RMSE=3.1284

📊 XGB 모델 학습 중...
✅ xgb: Val RMSE=2.5723, Test RMSE=2.5668

📊 CAT 모델 학습 중...
✅ cat: Val RMSE=2.5470, Test RMSE=2.5426

🏆 베스트 모델: RF
   Val RMSE: 2.5421
   Test RMSE: 2.5306
✅ 모델 S3 저장 완료: s3://weather-mlops-team-data/models/weather-predictor-003/
wandb:                                                                                
wandb: 
wandb: Run history:
wandb:    best_test_rmse ▁
wandb:     best_val_rmse ▁
wandb:      cat_test_mae ▁
wandb:     cat_test_rmse ▁
wandb:     cat_train_mae ▁
wandb:    cat_train_rmse ▁
wandb:       cat_val_mae ▁
wandb:      cat_val_rmse ▁
wandb:    lasso_test_mae ▁
wandb:   lasso_test_rmse ▁
wandb:   lasso_train_mae ▁
wandb:  lasso_train_rmse ▁
wandb:     lasso_val_mae ▁
wandb:    lasso_val_rmse ▁
wandb:     lgbm_test_mae ▁
wandb:    lgbm_test_rmse ▁
wandb:    lgbm_train_mae ▁
wandb:   lgbm_train_rmse ▁
wandb:      lgbm_val_mae ▁
wandb:     lgbm_val_rmse ▁
wandb:   linear_test_mae ▁
wandb:  linear_test_rmse ▁
wandb:  linear_train_mae ▁
wandb: linear_train_rmse ▁
wandb:    linear_val_mae ▁
wandb:   linear_val_rmse ▁
wandb:       rf_test_mae ▁
wandb:      rf_test_rmse ▁
wandb:      rf_train_mae ▁
wandb:     rf_train_rmse ▁
wandb:        rf_val_mae ▁
wandb:       rf_val_rmse ▁
wandb:    ridge_test_mae ▁
wandb:   ridge_test_rmse ▁
wandb:   ridge_train_mae ▁
wandb:  ridge_train_rmse ▁
wandb:     ridge_val_mae ▁
wandb:    ridge_val_rmse ▁
wandb:      xgb_test_mae ▁
wandb:     xgb_test_rmse ▁
wandb:     xgb_train_mae ▁
wandb:    xgb_train_rmse ▁
wandb:       xgb_val_mae ▁
wandb:      xgb_val_rmse ▁
wandb: 
wandb: Run summary:
wandb:        best_model rf
wandb:    best_test_rmse 2.53061
wandb:     best_val_rmse 2.54213
wandb:      cat_test_mae 2.21326
wandb:     cat_test_rmse 2.54259
wandb:     cat_train_mae 2.15323
wandb:    cat_train_rmse 2.47755
wandb:       cat_val_mae 2.21665
wandb:      cat_val_rmse 2.54702
wandb:    lasso_test_mae 3.71334
wandb:   lasso_test_rmse 4.54547
wandb:   lasso_train_mae 3.69338
wandb:  lasso_train_rmse 4.53412
wandb:     lasso_val_mae 3.69424
wandb:    lasso_val_rmse 4.52773
wandb:     lgbm_test_mae 2.62561
wandb:    lgbm_test_rmse 3.12842
wandb:    lgbm_train_mae 2.60891
wandb:   lgbm_train_rmse 3.1124
wandb:      lgbm_val_mae 2.62473
wandb:     lgbm_val_rmse 3.12569
wandb:   linear_test_mae 2.99964
wandb:  linear_test_rmse 3.63957
wandb:  linear_train_mae 2.98136
wandb: linear_train_rmse 3.62894
wandb:    linear_val_mae 2.98111
wandb:   linear_val_rmse 3.6223
wandb:       rf_test_mae 2.13861
wandb:      rf_test_rmse 2.53061
wandb:      rf_train_mae 0.78629
wandb:     rf_train_rmse 0.94726
wandb:        rf_val_mae 2.14889
wandb:       rf_val_rmse 2.54213
wandb:    ridge_test_mae 2.99964
wandb:   ridge_test_rmse 3.63956
wandb:   ridge_train_mae 2.98136
wandb:  ridge_train_rmse 3.62894
wandb:     ridge_val_mae 2.98111
wandb:    ridge_val_rmse 3.62229
wandb:      xgb_test_mae 2.22631
wandb:     xgb_test_rmse 2.56683
wandb:     xgb_train_mae 2.13897
wandb:    xgb_train_rmse 2.47089
wandb:       xgb_val_mae 2.23154
wandb:      xgb_val_rmse 2.57232
wandb: 
wandb: 🚀 View run weather-predictor-003 at: https://wandb.ai/realtheai-insight-/weather-predictor/runs/dikoytfx
wandb: Synced 5 W&B file(s), 0 media file(s), 0 artifact file(s) and 0 other file(s)
wandb: Find logs at: ./wandb/run-20250928_064947-dikoytfx/logs
🎉 학습 완료!
(RandomForestRegressor(random_state=42), {'train_rmse': 0.9472649446832658, 'val_rmse': 2.542128998044893, 'test_rmse': 2.5306089032420402, 'train_mae': 0.7862885644768859, 'val_mae': 2.148894817518248, 'test_mae': 2.1386110948905106})

```

## 2. 트리모델 집중 분석 실험. (이유: 전체 모델 돌릴 때 트리모델인 rf 점수가 가장 높아서.)

```
docker exec -it mlops-cloud-project-mlops-7-jupyter-1 bash -c "python /app/src/models/train.py --model_names='[\"rf\", \"xgb\", \"lgbm\", \"cat\"]'"

```
실험명: weather-predictor-004
모델: 트리 기반 4개 모델 (rf, xgb, lgbm, cat)
WANDB: realtheai-insight-/weather-predictor 프로젝트에 004번으로 기록
S3: s3://weather-mlops-team-data/models/weather-predictor-004/에 최고 모델 저장

목적: 성능이 우수한 트리 기반 모델들만 집중 분석
- 003 실험에서 선형 모델들(linear, ridge, lasso)은 성능이 떨어짐 (RMSE 3.6+)
- 트리 모델들은 모두 우수한 성능 (RMSE 2.5~3.1)
- 학습 시간 단축 및 유망 모델 집중 분석

### 결과

```
시드 42로 고정 완료
wandb: Currently logged in as: realtheai-insight (realtheai-insight-). Use `wandb login --relogin` to force relogin
wandb: wandb version 0.22.0 is available!  To upgrade, please run:
wandb:  $ pip install wandb --upgrade
wandb: Tracking run with wandb version 0.16.3
wandb: Run data is saved locally in /app/wandb/run-20250928_065450-3ukvxvt2
wandb: Run `wandb offline` to turn off syncing.
wandb: Syncing run weather-predictor-004
wandb: ⭐️ View project at https://wandb.ai/realtheai-insight-/weather-predictor
wandb: 🚀 View run at https://wandb.ai/realtheai-insight-/weather-predictor/runs/3ukvxvt2
🚀 모델 학습 시작...
🔄 S3에서 데이터 로드 중...
시드 42로 고정 완료
데이터 로드 완료: (342500, 34)
결측치 많은 컬럼 제거: ['rainfall']
원핫인코딩 적용: ['season', 'temp_category', 'pm10_grade', 'region']
피처: 29개, 샘플: 342500개
Train: (205500, 37), Val: (68500, 37), Test: (68500, 37)
✅ 데이터 분할 및 스케일링 완료

📊 RF 모델 학습 중...
✅ rf: Val RMSE=2.5421, Test RMSE=2.5306

📊 XGB 모델 학습 중...
✅ xgb: Val RMSE=2.5723, Test RMSE=2.5668

📊 LGBM 모델 학습 중...
✅ lgbm: Val RMSE=3.1257, Test RMSE=3.1284

📊 CAT 모델 학습 중...
✅ cat: Val RMSE=2.5470, Test RMSE=2.5426

🏆 베스트 모델: RF
   Val RMSE: 2.5421
   Test RMSE: 2.5306
✅ 모델 S3 저장 완료: s3://weather-mlops-team-data/models/weather-predictor-004/
wandb:                                                                                
wandb: 
wandb: Run history:
wandb:  best_test_rmse ▁
wandb:   best_val_rmse ▁
wandb:    cat_test_mae ▁
wandb:   cat_test_rmse ▁
wandb:   cat_train_mae ▁
wandb:  cat_train_rmse ▁
wandb:     cat_val_mae ▁
wandb:    cat_val_rmse ▁
wandb:   lgbm_test_mae ▁
wandb:  lgbm_test_rmse ▁
wandb:  lgbm_train_mae ▁
wandb: lgbm_train_rmse ▁
wandb:    lgbm_val_mae ▁
wandb:   lgbm_val_rmse ▁
wandb:     rf_test_mae ▁
wandb:    rf_test_rmse ▁
wandb:    rf_train_mae ▁
wandb:   rf_train_rmse ▁
wandb:      rf_val_mae ▁
wandb:     rf_val_rmse ▁
wandb:    xgb_test_mae ▁
wandb:   xgb_test_rmse ▁
wandb:   xgb_train_mae ▁
wandb:  xgb_train_rmse ▁
wandb:     xgb_val_mae ▁
wandb:    xgb_val_rmse ▁
wandb: 
wandb: Run summary:
wandb:      best_model rf
wandb:  best_test_rmse 2.53061
wandb:   best_val_rmse 2.54213
wandb:    cat_test_mae 2.21326
wandb:   cat_test_rmse 2.54259
wandb:   cat_train_mae 2.15323
wandb:  cat_train_rmse 2.47755
wandb:     cat_val_mae 2.21665
wandb:    cat_val_rmse 2.54702
wandb:   lgbm_test_mae 2.62561
wandb:  lgbm_test_rmse 3.12842
wandb:  lgbm_train_mae 2.60891
wandb: lgbm_train_rmse 3.1124
wandb:    lgbm_val_mae 2.62473
wandb:   lgbm_val_rmse 3.12569
wandb:     rf_test_mae 2.13861
wandb:    rf_test_rmse 2.53061
wandb:    rf_train_mae 0.78629
wandb:   rf_train_rmse 0.94726
wandb:      rf_val_mae 2.14889
wandb:     rf_val_rmse 2.54213
wandb:    xgb_test_mae 2.22631
wandb:   xgb_test_rmse 2.56683
wandb:   xgb_train_mae 2.13897
wandb:  xgb_train_rmse 2.47089
wandb:     xgb_val_mae 2.23154
wandb:    xgb_val_rmse 2.57232
wandb: 
wandb: 🚀 View run weather-predictor-004 at: https://wandb.ai/realtheai-insight-/weather-predictor/runs/3ukvxvt2
wandb: Synced 5 W&B file(s), 0 media file(s), 0 artifact file(s) and 0 other file(s)
wandb: Find logs at: ./wandb/run-20250928_065450-3ukvxvt2/logs
🎉 학습 완료!
(RandomForestRegressor(random_state=42), {'train_rmse': 0.9472649446832658, 'val_rmse': 2.542128998044893, 'test_rmse': 2.5306089032420402, 'train_mae': 0.7862885644768859, 'val_mae': 2.148894817518248, 'test_mae': 2.1386110948905106})

```
## 3. 데이터 분할 비율 실험


004 실험 결과 분석:
🏆 RF: 여전히 최고 성능 (Val RMSE: 2.5421)
🥈 CAT: 2위 (Val RMSE: 2.5470) - 근소한 차이
🥉 XGB: 3위 (Val RMSE: 2.5723)
LGBM: 4위 (Val RMSE: 3.1257)


결과 분석이 상위로 되어서 다음과 같이 실험 

목적: 더 큰 테스트셋으로 일반화 성능 확인
모델: 상위 3개만 (RF, XGB, CAT)

실험명: weather-predictor-005
모델: 상위 3개 모델 (rf, xgb, cat)
데이터 분할: test_size=0.3, val_size=0.15 (기존: test_size=0.2, val_size=0.2)
WANDB: realtheai-insight-/weather-predictor 프로젝트에 005번으로 기록
S3: s3://weather-mlops-team-data/models/weather-predictor-005/에 최고 모델 저장

목적: 데이터 분할 비율 변경으로 일반화 성능 확인
- 004 실험에서 상위 3개 모델 선정 (RF, XGB, CAT)
- 더 큰 테스트셋(30%)으로 진짜 성능 측정
- 검증셋은 15%로 줄여서 학습 데이터 확보
- LGBM 제외 (성능이 현저히 떨어짐)

```
docker exec -it mlops-cloud-project-mlops-7-jupyter-1 bash -c "python /app/src/models/train.py --model_names='["rf", "xgb", "cat"]' --test_size=0.3 --val_size=0.15"
```

### 결과

```
시드 42로 고정 완료
wandb: Currently logged in as: realtheai-insight (realtheai-insight-). Use `wandb login --relogin` to force relogin
wandb: wandb version 0.22.0 is available!  To upgrade, please run:
wandb:  $ pip install wandb --upgrade
wandb: Tracking run with wandb version 0.16.3
wandb: Run data is saved locally in /app/wandb/run-20250928_070341-zar7956t
wandb: Run `wandb offline` to turn off syncing.
wandb: Syncing run weather-predictor-005
wandb: ⭐️ View project at https://wandb.ai/realtheai-insight-/weather-predictor
wandb: 🚀 View run at https://wandb.ai/realtheai-insight-/weather-predictor/runs/zar7956t
🚀 모델 학습 시작...
🔄 S3에서 데이터 로드 중...
시드 42로 고정 완료
데이터 로드 완료: (342500, 34)
결측치 많은 컬럼 제거: ['rainfall']
원핫인코딩 적용: ['season', 'temp_category', 'pm10_grade', 'region']
피처: 29개, 샘플: 342500개
Train: (188374, 37), Val: (51376, 37), Test: (102750, 37)
✅ 데이터 분할 및 스케일링 완료

📊 RF 모델 학습 중...
✅ rf: Val RMSE=2.5500, Test RMSE=2.5422

📊 XGB 모델 학습 중...
✅ xgb: Val RMSE=2.5809, Test RMSE=2.5723

📊 CAT 모델 학습 중...
✅ cat: Val RMSE=2.5525, Test RMSE=2.5472

🏆 베스트 모델: RF
   Val RMSE: 2.5500
   Test RMSE: 2.5422
✅ 모델 S3 저장 완료: s3://weather-mlops-team-data/models/weather-predictor-005/
wandb:                                                                                
wandb: 
wandb: Run history:
wandb: best_test_rmse ▁
wandb:  best_val_rmse ▁
wandb:   cat_test_mae ▁
wandb:  cat_test_rmse ▁
wandb:  cat_train_mae ▁
wandb: cat_train_rmse ▁
wandb:    cat_val_mae ▁
wandb:   cat_val_rmse ▁
wandb:    rf_test_mae ▁
wandb:   rf_test_rmse ▁
wandb:   rf_train_mae ▁
wandb:  rf_train_rmse ▁
wandb:     rf_val_mae ▁
wandb:    rf_val_rmse ▁
wandb:   xgb_test_mae ▁
wandb:  xgb_test_rmse ▁
wandb:  xgb_train_mae ▁
wandb: xgb_train_rmse ▁
wandb:    xgb_val_mae ▁
wandb:   xgb_val_rmse ▁
wandb: 
wandb: Run summary:
wandb:     best_model rf
wandb: best_test_rmse 2.54222
wandb:  best_val_rmse 2.55004
wandb:   cat_test_mae 2.21483
wandb:  cat_test_rmse 2.54715
wandb:  cat_train_mae 2.14902
wandb: cat_train_rmse 2.47412
wandb:    cat_val_mae 2.21803
wandb:   cat_val_rmse 2.55247
wandb:    rf_test_mae 2.14911
wandb:   rf_test_rmse 2.54222
wandb:   rf_train_mae 0.78922
wandb:  rf_train_rmse 0.95001
wandb:     rf_val_mae 2.15594
wandb:    rf_val_rmse 2.55004
wandb:   xgb_test_mae 2.226
wandb:  xgb_test_rmse 2.57228
wandb:  xgb_train_mae 2.12717
wandb: xgb_train_rmse 2.46252
wandb:    xgb_val_mae 2.23067
wandb:   xgb_val_rmse 2.58089
wandb: 
wandb: 🚀 View run weather-predictor-005 at: https://wandb.ai/realtheai-insight-/weather-predictor/runs/zar7956t
wandb: Synced 5 W&B file(s), 0 media file(s), 0 artifact file(s) and 0 other file(s)
wandb: Find logs at: ./wandb/run-20250928_070341-zar7956t/logs
🎉 학습 완료!
(RandomForestRegressor(random_state=42), {'train_rmse': 0.9500130204807133, 'val_rmse': 2.5500411313517968, 'test_rmse': 2.5422199179920533, 'train_mae': 0.7892185227260665, 'val_mae': 2.1559353589224544, 'test_mae': 2.1491148418491486})
```


## 3. 다른 시드 안정성 테스트 (006)


005 실험 결과 분석:
성능 비교 (004 vs 005):
RF: Val 2.5421 → 2.5500 (소폭 하락, 하지만 Test는 2.5306 → 2.5422로 비슷)
CAT: Val 2.5470 → 2.5525 (소폭 하락)
XGB: Val 2.5723 → 2.5809 (소폭 하락)
중요한 발견:
더 큰 테스트셋(30%)에서도 RF가 여전히 최고!
성능이 안정적 - 데이터 분할 변경에도 순위 유지
RF의 일관성 확인됨


실험명: weather-predictor-006
모델: 상위 2개 모델 (rf, cat
설정: random_state=999 (기존: random_state=42)
WANDB: realtheai-insight-/weather-predictor 프로젝트에 006번으로 기록
S3: s3://weather-mlops-team-data/models/weather-predictor-006/에 최고 모델 저장

목적: 시드 변경으로 모델 성능 안정성 확인
- 005 실험에서 RF가 지속적으로 최고 성능 유지
- 다른 랜덤 시드로 결과 재현성 및 안정성 테스트
- 상위 2개 모델만 선정 (RF, CAT)
- XGB 제외 (성능 차이가 명확함)

코드드
```
docker exec -it mlops-cloud-project-mlops-7-jupyter-1 bash -c "python /app/src/models/train.py --model_names='[\"rf\", \"cat\"]' --random_state=999"
```

### 결과

```
시드 999로 고정 완료
wandb: Currently logged in as: realtheai-insight (realtheai-insight-). Use `wandb login --relogin` to force relogin
wandb: wandb version 0.22.0 is available!  To upgrade, please run:
wandb:  $ pip install wandb --upgrade
wandb: Tracking run with wandb version 0.16.3
wandb: Run data is saved locally in /app/wandb/run-20250928_070949-f6yv4orh
wandb: Run `wandb offline` to turn off syncing.
wandb: Syncing run weather-predictor-006
wandb: ⭐️ View project at https://wandb.ai/realtheai-insight-/weather-predictor
wandb: 🚀 View run at https://wandb.ai/realtheai-insight-/weather-predictor/runs/f6yv4orh
🚀 모델 학습 시작...
🔄 S3에서 데이터 로드 중...
시드 999로 고정 완료
데이터 로드 완료: (342500, 34)
결측치 많은 컬럼 제거: ['rainfall']
원핫인코딩 적용: ['season', 'temp_category', 'pm10_grade', 'region']
피처: 29개, 샘플: 342500개
Train: (205500, 37), Val: (68500, 37), Test: (68500, 37)
✅ 데이터 분할 및 스케일링 완료

📊 RF 모델 학습 중...
✅ rf: Val RMSE=2.5325, Test RMSE=2.5351

📊 CAT 모델 학습 중...
✅ cat: Val RMSE=2.5420, Test RMSE=2.5374

🏆 베스트 모델: RF
   Val RMSE: 2.5325
   Test RMSE: 2.5351
✅ 모델 S3 저장 완료: s3://weather-mlops-team-data/models/weather-predictor-006/
wandb:                                                                                
wandb: 
wandb: Run history:
wandb: best_test_rmse ▁
wandb:  best_val_rmse ▁
wandb:   cat_test_mae ▁
wandb:  cat_test_rmse ▁
wandb:  cat_train_mae ▁
wandb: cat_train_rmse ▁
wandb:    cat_val_mae ▁
wandb:   cat_val_rmse ▁
wandb:    rf_test_mae ▁
wandb:   rf_test_rmse ▁
wandb:   rf_train_mae ▁
wandb:  rf_train_rmse ▁
wandb:     rf_val_mae ▁
wandb:    rf_val_rmse ▁
wandb: 
wandb: Run summary:
wandb:     best_model rf
wandb: best_test_rmse 2.53506
wandb:  best_val_rmse 2.53245
wandb:   cat_test_mae 2.20856
wandb:  cat_test_rmse 2.53736
wandb:  cat_train_mae 2.15651
wandb: cat_train_rmse 2.47958
wandb:    cat_val_mae 2.21024
wandb:   cat_val_rmse 2.54198
wandb:    rf_test_mae 2.14149
wandb:   rf_test_rmse 2.53506
wandb:   rf_train_mae 0.78781
wandb:  rf_train_rmse 0.94766
wandb:     rf_val_mae 2.13862
wandb:    rf_val_rmse 2.53245
wandb: 
wandb: 🚀 View run weather-predictor-006 at: https://wandb.ai/realtheai-insight-/weather-predictor/runs/f6yv4orh
wandb: Synced 5 W&B file(s), 0 media file(s), 0 artifact file(s) and 0 other file(s)
wandb: Find logs at: ./wandb/run-20250928_070949-f6yv4orh/logs
🎉 학습 완료!
(RandomForestRegressor(random_state=42), {'train_rmse': 0.9476596350061298, 'val_rmse': 2.53245068030459, 'test_rmse': 2.535064760686778, 'train_mae': 0.7878124330900244, 'val_mae': 2.138616204379562, 'test_mae': 2.1414902189781024})
realtheai@PSH:~/mlops-cloud-project-mlops-7$ 
```
006 실험 결과 분석:
RF 성능 안정성 확인:
시드 42: Val RMSE 2.5421 → 시드 999: Val RMSE 2.5325 ✅ (약간 개선!)
시드 42: Test RMSE 2.5306 → 시드 999: Test RMSE 2.5351 ✅ (거의 동일)
중요한 발견:
🏆 RF가 여전히 최고 성능! (시드에 관계없이 일관성)
📊 성능 안정성 확인 - 시드 변경에도 비슷한 성능
🎯 RF의 신뢰성 - 다양한 조건에서도 최고 모델 유지
전체 실험 요약:
001-003: 전체 모델 비교 → RF 최고
004: 트리 모델만 → RF 최고
005: 데이터 분할 변경 → RF 최고
006: 시드 변경 → RF 최고
결론: Random Forest가 가장 안정적이고 우수한 모델! 🌟

다음 단계 :
RF 하이퍼파라미터 튜닝 - 성능 더 개선

앙상블 - RF + CAT 조합

## 다음 단계에서  할 예정


RF 하이퍼파라미터 튜닝 - 성능 더 개선 (train.py 코드 수정되어야 함.)

앙상블 - RF + CAT 조합

(별도 튜닝 코드)의 장점:
✅ 역할 분리 - train.py는 기본 비교, tune.py는 최적화
✅ 깔끔한 구조 - 각 파일의 목적이 명확
✅ GridSearch/RandomSearch 등 전문 도구 사용 가능
✅ 기존 코드 보존 - train.py는 그대로 유지
✅ 확장성 - 나중에 Optuna, Hyperopt 등도 추가 가능

--------
성능 비교:
003: Val RMSE 2.5421, Test RMSE 2.5306
004: Val RMSE 2.5421, Test RMSE 2.5306 (003과 동일)
005: Val RMSE 2.5500, Test RMSE 2.5422 (데이터 분할 변경)
006: Val RMSE 2.5325, Test RMSE 2.5351 ⭐ 최고 성능
006번 모델의 장점:
✅ 최고 검증 성능 - Val RMSE 2.5325 (가장 낮음)
✅ 안정성 확인 - 시드 변경(999)에도 우수한 성능
✅ 재현성 - 다른 조건에서도 RF가 최고임을 증명
✅ 신뢰성 - 여러 실험을 통해 검증된 모델

-------------


예정:
train.py: 기본 모델 비교 및 베이스라인
tune.py: 하이퍼파라미터 최적화 전용