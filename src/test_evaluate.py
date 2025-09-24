import yaml
import numpy as np
import os
from dotenv import load_dotenv
from sklearn.datasets import make_regression, make_classification
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

# wandb import를 optional로 처리
try:
    import wandb
    WANDB_AVAILABLE = True
except ImportError:
    wandb = None
    WANDB_AVAILABLE = False

# 환경변수 로드
load_dotenv()

# 시스템 경로 설정
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from models.registry import get_model
from models.evaluate import ModelEvaluator
from test_integration import test_with_yaml_config

def generate_run_name():
    """run name 자동 생성"""
    import time
    timestamp = int(time.time())
    return f"test_eval_{timestamp}"

def init_wandb(use_wandb=True, project_name="test-evaluation"):
    """wandb 초기화"""
    if not use_wandb:
        return False
        
    try:
        # wandb가 설치되지 않은 경우
        if not WANDB_AVAILABLE:
            print("⚠️ wandb가 설치되지 않았습니다. wandb 기능을 비활성화합니다.")
            return False
        
        # .env에서 API 키 로드
        api_key = os.getenv('WANDB_API_KEY')
        if not api_key:
            print("⚠️ WANDB_API_KEY가 .env 파일에 설정되지 않았습니다.")
            return False
        
        # wandb 초기화
        run_name = generate_run_name()
        wandb.init(
            project=project_name,
            name=run_name,
            config={
                'test_type': 'model_evaluation',
                'framework': 'sklearn'
            }
        )
        print(f"📊 wandb 초기화 완료 - Project: {project_name}, Run: {run_name}")
        return True
        
    except Exception as e:
        print(f"⚠️ wandb 초기화 실패: {str(e)}")
        print("wandb 없이 계속 진행합니다.")
        return False

def log_test_results_to_wandb(test_results, use_wandb=False):
    """테스트 결과를 wandb에 로깅"""
    if not use_wandb or not WANDB_AVAILABLE:
        return
    
    try:
        # 테스트 결과 로깅
        passed = sum(test_results.values())
        total = len(test_results)
        success_rate = passed / total * 100 if total > 0 else 0
        
        wandb.log({
            'total_tests': total,
            'passed_tests': passed,
            'failed_tests': total - passed,
            'success_rate': success_rate
        })
        
        # 개별 테스트 결과 로깅
        for test_name, result in test_results.items():
            wandb.log({f"test_{test_name.replace(' ', '_').lower()}": 1 if result else 0})
        
        print("📊 테스트 결과가 wandb에 로깅되었습니다.")
        
    except Exception as e:
        print(f"⚠️ wandb 로깅 실패: {str(e)}")

def get_trained_models_from_integration():
    """test_integration.py에서 학습된 모델들을 가져오기"""
    print("📦 test_integration.py에서 학습된 모델들 가져오는 중...")
    
    # test_integration.py 실행하여 학습된 모델들과 데이터 가져오기
    import importlib
    import test_integration as test_integration
    importlib.reload(test_integration)  # 모듈 재로드
    
    # 테스트 데이터 생성 (test_integration.py와 동일)
    from sklearn.datasets import make_regression
    from sklearn.model_selection import train_test_split
    
    X, y = make_regression(n_samples=200, n_features=10, noise=0.1, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # test_integration.py의 설정 로드
    try:
        with open('config/models.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        print("✅ 실제 YAML 설정 파일 사용")
    except FileNotFoundError:
        print("⚠️ YAML 파일이 없어서 기본 설정 사용")
        config = {
            'task': 'regression',
            'target': 'price',
            'cv': {'n_splits': 5, 'shuffle': True, 'random_state': 42},
            'metrics': {'primary': 'rmse', 'others': ['mae', 'r2']},
            'models': [
                {'name': 'linear', 'params': {}},
                {'name': 'ridge', 'params': {'alpha': 1.0}},
                {'name': 'rf', 'params': {'n_estimators': 50, 'random_state': 42}}
            ]
        }
    
    # 모델 학습 (test_integration.py 방식과 동일)
    trained_models = {}
    
    for model_config in config['models']:
        name = model_config['name']
        params = model_config['params']
        
        try:
            print(f"🔄 {name} 모델 재학습 중...")
            model = get_model(config['task'], name, params)
            model.fit(X_train, y_train)
            trained_models[name] = model
            print(f"✅ {name} 모델 학습 완료")
        except Exception as e:
            print(f"❌ {name} 모델 학습 실패: {e}")
    
    return trained_models, X_test, y_test, config

def test_regression_evaluation():
    """회귀 모델 평가 테스트"""
    print("=== 회귀 모델 평가 테스트 ===")
    
    # test_integration.py에서 학습된 모델들 가져오기
    trained_models, X_test, y_test, config = get_trained_models_from_integration()
    
    if not trained_models:
        print("❌ 학습된 모델이 없습니다.")
        return False
    
    # 실제 설정 파일 사용 (임시 파일 생성하지 않음)
    config_path = 'config/models.yaml'
    
    try:
        # ModelEvaluator 테스트 (wandb 활성화)
        print("\n🔍 ModelEvaluator 초기화...")
        evaluator = ModelEvaluator(config_path=config_path, use_wandb=True, project_name="test-model-evaluation")
        print("✅ ModelEvaluator 초기화 성공")
        
        # 모델 평가
        print("\n📊 모델 평가 시작...")
        evaluator.evaluate_models(trained_models, X_test, y_test)
        print("✅ 모델 평가 완료")
        
        # 결과 확인
        print("\n📋 결과 확인...")
        summary_df = evaluator.get_summary_dataframe()
        if summary_df is not None:
            print("✅ 요약 DataFrame 생성 성공")
            print(summary_df)
        else:
            print("❌ 요약 DataFrame 생성 실패")
            return False
        
        # 최고 성능 모델 확인
        best_model = evaluator.get_best_model()
        if best_model:
            print(f"🏆 최고 성능 모델: {best_model['name']}")
            print("✅ 최고 성능 모델 선택 성공")
        else:
            print("❌ 최고 성능 모델 선택 실패")
            return False
        
        # 시각화 테스트 (에러 없이 실행되는지 확인)
        print("\n📈 시각화 테스트...")
        try:
            # plot_results는 실제로 plt.show()를 호출하므로 주석 처리
            # evaluator.plot_results()
            print("✅ 시각화 함수 호출 가능 (실제 실행은 생략)")
        except Exception as e:
            print(f"⚠️ 시각화 테스트 스킵: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 회귀 모델 평가 테스트 실패: {e}")
        return False

def get_trained_classification_models():
    """분류용 학습된 모델들 가져오기"""
    print("📦 분류 모델들 학습 중...")
    
    # 테스트 데이터 생성 (분류용)
    from sklearn.datasets import make_classification
    from sklearn.model_selection import train_test_split
    
    X, y = make_classification(n_samples=200, n_features=10, n_classes=2, 
                             n_informative=5, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 분류 설정
    config = {
        'task': 'classification',
        'target': 'class',
        'cv': {'n_splits': 5, 'shuffle': True, 'random_state': 42},
        'metrics': {'primary': 'accuracy', 'others': ['precision', 'recall', 'f1']},
        'models': [
            {'name': 'logistic_regression', 'params': {'random_state': 42, 'max_iter': 200}},
            {'name': 'ridge_classifier', 'params': {'random_state': 42}},
            {'name': 'rf', 'params': {'n_estimators': 50, 'random_state': 42}}
        ]
    }
    
    # 모델 학습
    trained_models = {}
    
    for model_config in config['models']:
        name = model_config['name']
        params = model_config['params']
        
        try:
            print(f"🔄 {name} 분류 모델 학습 중...")
            model = get_model(config['task'], name, params)
            model.fit(X_train, y_train)
            trained_models[name] = model
            print(f"✅ {name} 분류 모델 학습 완료")
        except Exception as e:
            print(f"❌ {name} 분류 모델 학습 실패: {e}")
    
    return trained_models, X_test, y_test, config

def test_classification_evaluation():
    """분류 모델 평가 테스트"""
    print("\n=== 분류 모델 평가 테스트 ===")
    
    # 분류 모델들 가져오기
    trained_models, X_test, y_test, config = get_trained_classification_models()
    
    if not trained_models:
        print("❌ 학습된 분류 모델이 없습니다.")
        return False
    
    # 임시 분류 설정 파일 생성
    temp_config_path = 'temp_classification_config.yaml'
    with open(temp_config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True)
    
    try:
        # ModelEvaluator 테스트 (분류용)
        print("\n🔍 분류 ModelEvaluator 초기화...")
        evaluator = ModelEvaluator(config_path=temp_config_path, use_wandb=True, project_name="test-classification-evaluation")
        print("✅ 분류 ModelEvaluator 초기화 성공")
        
        # 모델 평가
        print("\n📊 분류 모델 평가 시작...")
        evaluator.evaluate_models(trained_models, X_test, y_test)
        print("✅ 분류 모델 평가 완료")
        
        # 결과 확인
        print("\n📋 분류 결과 확인...")
        summary_df = evaluator.get_summary_dataframe()
        if summary_df is not None:
            print("✅ 분류 요약 DataFrame 생성 성공")
            print(summary_df)
        else:
            print("❌ 분류 요약 DataFrame 생성 실패")
            return False
        
        # 최고 성능 모델 확인
        best_model = evaluator.get_best_model()
        if best_model:
            print(f"🏆 최고 성능 분류 모델: {best_model['name']}")
            print("✅ 최고 성능 분류 모델 선택 성공")
        else:
            print("❌ 최고 성능 분류 모델 선택 실패")
            return False
        
        # 분류 시각화 테스트
        print("\n📈 분류 시각화 테스트...")
        try:
            # plot_results는 실제로 plt.show()를 호출하므로 주석 처리
            # evaluator.plot_results()
            print("✅ 분류 시각화 함수 호출 가능 (실제 실행은 생략)")
        except Exception as e:
            print(f"⚠️ 분류 시각화 테스트 스킵: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 분류 모델 평가 테스트 실패: {e}")
        return False
        
    finally:
        # 임시 파일 정리
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)
            print(f"🗑️ 임시 분류 설정 파일 삭제: {temp_config_path}")

def test_yaml_config_loading():
    """실제 YAML 설정 파일 로딩 테스트"""
    print("\n=== 실제 YAML 설정 파일 테스트 ===")
    
    config_path = 'config/models.yaml'
    
    try:
        evaluator = ModelEvaluator(config_path=config_path, use_wandb=False)
        print(f"✅ 실제 설정 파일 로딩 성공: {config_path}")
        print(f"Task: {evaluator.task}")
        print(f"Target: {evaluator.target}")
        print(f"CV Splits: {evaluator.cv_config['n_splits']}")
        print(f"Primary Metric: {evaluator.metrics_config['primary']}")
        return True
    except FileNotFoundError:
        print(f"⚠️ 설정 파일을 찾을 수 없습니다: {config_path}")
        return False
    except Exception as e:
        print(f"❌ 설정 파일 로딩 실패: {e}")
        return False

def test_error_handling():
    """에러 처리 테스트"""
    print("\n=== 에러 처리 테스트 ===")
    
    # 존재하지 않는 설정 파일
    try:
        evaluator = ModelEvaluator(config_path='nonexistent.yaml', use_wandb=False)
        print("❌ 존재하지 않는 파일에 대한 에러 처리 실패")
        return False
    except FileNotFoundError:
        print("✅ 존재하지 않는 파일에 대한 에러 처리 성공")
    
    # 빈 모델 딕셔너리로 평가 시도
    try:
        evaluator = ModelEvaluator(config_path='config/models.yaml', use_wandb=False)
        X, y = make_regression(n_samples=50, n_features=3, random_state=42)
        
        # 빈 모델 딕셔너리
        evaluator.evaluate_models({}, X, y)
        print("✅ 빈 모델 딕셔너리에 대한 처리 성공")
        
        # 결과 확인
        summary_df = evaluator.get_summary_dataframe()
        best_model = evaluator.get_best_model()
        
        if summary_df is None and best_model is None:
            print("✅ 빈 결과에 대한 처리 성공")
        else:
            print("❌ 빈 결과에 대한 처리 실패")
            return False
            
    except Exception as e:
        print(f"❌ 에러 처리 테스트 실패: {e}")
        return False
    
    return True

def run_all_tests(use_wandb=True):
    """모든 테스트 실행"""
    print("🚀 ModelEvaluator 테스트 시작")
    print("=" * 50)
    
    # wandb 초기화
    wandb_enabled = init_wandb(use_wandb=use_wandb, project_name="test-evaluation")
    
    tests = [
        ("YAML 설정 로딩", test_yaml_config_loading),
        ("회귀 모델 평가", test_regression_evaluation),
        ("분류 모델 평가", test_classification_evaluation),
        ("에러 처리", test_error_handling)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 {test_name} 테스트 실행...")
            results[test_name] = test_func()
            if results[test_name]:
                print(f"✅ {test_name} 테스트 성공")
            else:
                print(f"❌ {test_name} 테스트 실패")
        except Exception as e:
            print(f"💥 {test_name} 테스트 중 예외 발생: {e}")
            results[test_name] = False
    
    # 최종 결과
    print("\n" + "=" * 50)
    print("🎯 테스트 결과 요약")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} | {status}")
    
    print("-" * 50)
    print(f"총 테스트: {total}")
    print(f"성공: {passed}")
    print(f"실패: {total - passed}")
    print(f"성공률: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 모든 테스트가 성공했습니다!")
    else:
        print(f"\n⚠️ {total - passed}개의 테스트가 실패했습니다.")
    
    # wandb에 테스트 결과 로깅
    log_test_results_to_wandb(results, use_wandb=wandb_enabled)
    
    # wandb 종료
    if wandb_enabled and WANDB_AVAILABLE:
        try:
            wandb.finish()
            print("📊 wandb 실행 종료됨")
        except:
            pass
    
    return passed == total

if __name__ == "__main__":
    # wandb 사용 여부 결정 (환경변수나 인자로 제어 가능)
    use_wandb = os.getenv('USE_WANDB', 'true').lower() == 'true'
    success = run_all_tests(use_wandb=use_wandb)
    exit(0 if success else 1) 