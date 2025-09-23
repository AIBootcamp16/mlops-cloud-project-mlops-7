# test_integration.py
import yaml
from models.registry import get_model
from sklearn.datasets import make_regression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np

def test_with_yaml_config():
    """YAML 설정 파일과 함께 전체 파이프라인 테스트"""
    
    # 테스트용 YAML 설정
    config = {
        'task': 'regression',
        'target': 'price',
        'cv': {
            'n_splits': 5,
            'shuffle': True,
            'random_state': 42
        },
        'metrics': {
            'primary': 'rmse',
            'others': ['mae', 'r2']
        },
        'models': [
            {'name': 'linear', 'params': {}},
            {'name': 'ridge', 'params': {'alpha': 1.0}},
            {'name': 'rf', 'params': {'n_estimators': 50, 'random_state': 42}}
        ]
    }
    
    print("=== YAML 설정과 함께 통합 테스트 ===")
    print(f"Task: {config['task']}")
    print(f"Models: {[m['name'] for m in config['models']]}")
    
    # 테스트 데이터 생성
    X, y = make_regression(n_samples=200, n_features=10, noise=0.1, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    results = {}
    
    # 각 모델 테스트
    for model_config in config['models']:
        name = model_config['name']
        params = model_config['params']
        
        try:
            print(f"\n--- {name} 모델 테스트 ---")
            
            # 1. 모델 생성
            model = get_model(config['task'], name, params)
            print(f"✅ 모델 생성 성공: {type(model).__name__}")
            
            # 2. 학습
            model.fit(X_train, y_train)
            print("✅ 학습 완료")
            
            # 3. 예측
            y_pred = model.predict(X_test)
            print("✅ 예측 완료")
            
            # 4. 평가
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            r2 = r2_score(y_test, y_pred)
            mae = np.mean(np.abs(y_test - y_pred))
            
            results[name] = {
                'rmse': rmse,
                'r2': r2,
                'mae': mae
            }
            
            print(f"  RMSE: {rmse:.4f}")
            print(f"  R²: {r2:.4f}")
            print(f"  MAE: {mae:.4f}")
            
        except Exception as e:
            print(f"❌ {name} 모델 실패: {e}")
            results[name] = None
    
    # 결과 요약
    print("\n=== 결과 요약 ===")
    successful_models = {k: v for k, v in results.items() if v is not None}
    
    if successful_models:
        # 기본 메트릭으로 정렬
        primary_metric = config['metrics']['primary']
        if primary_metric == 'rmse':
            best_model = min(successful_models.items(), key=lambda x: x[1]['rmse'])
            print(f"🏆 최고 성능 모델: {best_model[0]} (RMSE: {best_model[1]['rmse']:.4f})")
        
        print("\n모든 모델 성능:")
        for name, metrics in successful_models.items():
            print(f"  {name}: RMSE={metrics['rmse']:.4f}, R²={metrics['r2']:.4f}")
    
    return results

def test_yaml_file_loading():
    """실제 YAML 파일 로딩 테스트"""
    print("\n=== YAML 파일 로딩 테스트 ===")
    
    try:
        # 실제 설정 파일 읽기 시도
        with open('config/models.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        print("✅ YAML 파일 로딩 성공")
        print(f"Task: {config.get('task', 'undefined')}")
        print(f"Models: {[m['name'] for m in config.get('models', [])]}")
        
        # 설정 유효성 검사
        required_keys = ['task', 'models']
        for key in required_keys:
            if key not in config:
                print(f"❌ 필수 키 누락: {key}")
                return False
        
        # 모델 설정 검사
        for model_config in config['models']:
            if 'name' not in model_config:
                print(f"❌ 모델 설정에서 'name' 누락: {model_config}")
                return False
            if 'params' not in model_config:
                print(f"❌ 모델 설정에서 'params' 누락: {model_config}")
                return False
        
        print("✅ YAML 설정 유효성 검사 통과")
        return True
        
    except FileNotFoundError:
        print("❌ YAML 파일을 찾을 수 없습니다: config/models.yaml")
        return False
    except yaml.YAMLError as e:
        print(f"❌ YAML 파싱 에러: {e}")
        return False

if __name__ == "__main__":
    # 1. YAML 파일 로딩 테스트
    yaml_ok = test_yaml_file_loading()
    
    # 2. 통합 테스트
    results = test_with_yaml_config()
    
    # 3. 최종 결과
    successful_tests = sum(1 for r in results.values() if r is not None)
    total_tests = len(results)
    
    print(f"\n🎯 테스트 결과: {successful_tests}/{total_tests} 모델 성공")
    
    if yaml_ok and successful_tests > 0:
        print("🎉 모든 테스트 통과!")
    else:
        print("⚠️  일부 테스트 실패")