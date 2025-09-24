import numpy as np
import pandas as pd
import os
from dotenv import load_dotenv

# wandb import를 optional로 처리
try:
    import wandb
    WANDB_AVAILABLE = True
except ImportError:
    wandb = None
    WANDB_AVAILABLE = False

# matplotlib 설정을 import 전에 먼저 설정
import matplotlib
matplotlib.use('Agg')  # GUI 백엔드 비활성화
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 한글 폰트 설정 (import 직후)
plt.rcParams['font.family'] = ['Noto Sans CJK KR', 'Noto Sans CJK JP', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

import seaborn as sns
import yaml
from pathlib import Path
from sklearn.model_selection import cross_val_score
from sklearn.metrics import (
    mean_squared_error, mean_absolute_error, r2_score,
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, roc_auc_score, roc_curve
)
from sklearn.datasets import make_regression, make_classification
import warnings
warnings.filterwarnings('ignore')

# 환경변수 로드
load_dotenv()

# 시스템 경로 설정
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def generate_run_name():
    """run name 자동 생성"""
    import time
    timestamp = int(time.time())
    return f"model_eval_{timestamp}"

class ModelEvaluator:
    """학습된 모델 평가 및 시각화 전용 클래스 (wandb 통합)"""
    
    def __init__(self, config_path='conf/models.yaml', use_wandb=False, project_name="model-evaluation"):
        """
        Args:
            config_path: 모델 설정 파일 경로
            use_wandb: wandb 사용 여부
            project_name: wandb 프로젝트 이름
        """
        self.config = self._load_config(config_path)
        self.task = self.config['task']
        self.target = self.config['target']
        self.cv_config = self.config['cv']
        self.metrics_config = self.config['metrics']
        
        self.results = {}
        self.trained_models = {}
        
        # wandb 설정 (페이지 방식 따라 단순화)
        self.use_wandb = use_wandb
        if self.use_wandb:
            self._init_wandb(project_name)
    
    def _init_wandb(self, project_name):
        """wandb 초기화 - 페이지 방식 따라 단순화"""
        try:
            # wandb가 설치되지 않은 경우
            if not WANDB_AVAILABLE:
                print("⚠️ wandb가 설치되지 않았습니다. wandb 기능을 비활성화합니다.")
                self.use_wandb = False
                return
            
            # .env에서 API 키 로드
            api_key = os.getenv('WANDB_API_KEY')
            if not api_key:
                print("⚠️ WANDB_API_KEY가 .env 파일에 설정되지 않았습니다.")
                self.use_wandb = False
                return
            
            # wandb 초기화 (페이지의 간단한 방식 사용)
            run_name = generate_run_name()
            wandb.init(
                project=project_name,
                name=run_name,
                config={
                    'task': self.task,
                    'target': self.target,
                    'cv_splits': self.cv_config['n_splits'],
                    'primary_metric': self.metrics_config['primary']
                }
            )
            print(f"📊 wandb 초기화 완료 - Project: {project_name}, Run: {run_name}")
            
        except Exception as e:
            print(f"⚠️ wandb 초기화 실패: {str(e)}")
            print("use_wandb=False로 설정하고 계속 진행합니다.")
            self.use_wandb = False
        
    def _load_config(self, config_path):
        """YAML 설정 파일 로드"""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        print(f"📁 설정 파일 로드 완료: {config_path}")
        return config
    
    def evaluate_models(self, trained_models, X, y):
        """
        이미 학습된 모델들을 평가 (평가만 수행)
        
        Args:
            trained_models: {model_name: trained_model} 형태의 딕셔너리
            X: 특성 데이터  
            y: 타깃 데이터
        """
        print(f"🔍 {self.task.upper()} 모델 평가 시작...")
        print(f"타깃: {self.target}")
        print(f"데이터 크기: {X.shape}")
        print(f"평가할 모델 수: {len(trained_models)}")
        print("-" * 60)
        
        for model_name, model in trained_models.items():
            print(f"📊 {model_name.upper()} 모델 평가 중...")
            
            try:
                # 예측 (학습된 모델로)
                y_pred = model.predict(X)
                
                # 교차검증
                cv_scores = cross_val_score(
                    model, X, y, 
                    cv=self.cv_config['n_splits'],
                    scoring=self._get_cv_scoring()
                )
                
                # 결과 저장
                self.trained_models[model_name] = model
                self.results[model_name] = {
                    'y_true': y,
                    'y_pred': y_pred,
                    'cv_scores': cv_scores,
                    'cv_mean': cv_scores.mean(),
                    'cv_std': cv_scores.std(),
                    'model': model
                }
                
                # 태스크별 메트릭 계산
                if self.task == 'regression':
                    self._calculate_regression_metrics(model_name, y, y_pred)
                else:
                    self._calculate_classification_metrics(model_name, y, y_pred, model, X)
                
                # wandb 로깅 (페이지 방식 따라 단순화)
                if self.use_wandb:
                    self._log_metrics_to_wandb(model_name)
                
                print(f"✅ {model_name} 평가 완료!")
                
            except Exception as e:
                print(f"❌ {model_name} 평가 오류: {str(e)}")
                continue
        
        print("\n🎉 모든 모델 평가 완료!")
        self._print_summary()
        
        # wandb에 최종 요약 로깅
        if self.use_wandb:
            self._log_final_summary()
    
    def _log_metrics_to_wandb(self, model_name):
        """wandb에 메트릭 로깅 - 페이지 방식에 따라 단순화"""
        try:
            result = self.results[model_name]
            
            # 기본 메트릭 로깅
            log_dict = {
                f"{model_name}_cv_mean": result['cv_mean'],
                f"{model_name}_cv_std": result['cv_std']
            }
            
            if self.task == 'regression':
                log_dict.update({
                    f"{model_name}_rmse": result['rmse'],
                    f"{model_name}_mae": result['mae'],
                    f"{model_name}_r2": result['r2']
                })
            else:
                log_dict.update({
                    f"{model_name}_accuracy": result['accuracy'],
                    f"{model_name}_precision": result['precision'],
                    f"{model_name}_recall": result['recall'], # 재현율. 실제 양성인 것 중 양성으로 예측한 비율. 작을수록 좋음.
                    f"{model_name}_f1": result['f1'] # 정밀도와 재현율의 조화평균. 작을수록 좋음.
                })
                
                # ROC AUC 있는 경우 추가
                if 'roc_auc' in result:
                    log_dict[f"{model_name}_roc_auc"] = result['roc_auc']
            
            wandb.log(log_dict)
            
        except Exception as e:
            print(f"⚠️ wandb 메트릭 로깅 오류: {str(e)}")
    
    def _log_final_summary(self):
        """최종 요약 wandb 로깅"""
        try:
            # 최고 성능 모델 정보
            best_model_info = self.get_best_model()
            if best_model_info:
                wandb.log({
                    "best_model_name": best_model_info['name'],
                    f"best_{self.metrics_config['primary']}": best_model_info['metrics'][self.metrics_config['primary']]
                })
            
            # 모델 성능 비교 테이블
            summary_df = self.get_summary_dataframe()
            if summary_df is not None:
                wandb.log({"model_comparison": wandb.Table(dataframe=summary_df)})
                
        except Exception as e:
            print(f"⚠️ wandb 최종 요약 로깅 오류: {str(e)}")
    
    def _get_cv_scoring(self):
        """교차검증 스코어링 방법"""
        if self.task == 'regression':
            primary_metric = self.metrics_config['primary']
            if primary_metric == 'rmse':
                return 'neg_mean_squared_error'
            elif primary_metric == 'mae':
                return 'neg_mean_absolute_error'
            elif primary_metric == 'r2':
                return 'r2'
        else:
            return 'accuracy'
    
    def _calculate_regression_metrics(self, model_name, y_true, y_pred):
        """회귀 메트릭 계산"""
        self.results[model_name].update({
            'mse': mean_squared_error(y_true, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
            'mae': mean_absolute_error(y_true, y_pred),
            'r2': r2_score(y_true, y_pred)
        })
    
    def _calculate_classification_metrics(self, model_name, y_true, y_pred, model, X):
        """분류 메트릭 계산"""
        self.results[model_name].update({
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, average='weighted'),
            'recall': recall_score(y_true, y_pred, average='weighted'),
            'f1': f1_score(y_true, y_pred, average='weighted')
        })
        
        # ROC AUC (이진분류인 경우)
        if len(np.unique(y_true)) == 2:
            if hasattr(model, 'predict_proba'):
                y_proba = model.predict_proba(X)[:, 1]
                self.results[model_name]['roc_auc'] = roc_auc_score(y_true, y_proba)
                self.results[model_name]['y_proba'] = y_proba
    
    def _print_summary(self):
        """결과 요약 출력"""
        print("\n📊 모델 성능 요약:")
        print("=" * 80)
        
        if self.task == 'regression':
            primary_metric = self.metrics_config['primary']
            print(f"{'모델':^15} | {'RMSE':^10} | {'MAE':^10} | {'R²':^10} | {'CV Score':^15}")
            print("-" * 80)
            
            for name, result in self.results.items():
                cv_score = result['cv_mean']
                if primary_metric == 'rmse':
                    cv_score = np.sqrt(-cv_score)  # neg_mse를 rmse로 변환
                elif primary_metric == 'mae':
                    cv_score = -cv_score  # neg_mae를 mae로 변환
                
                print(f"{name:^15} | {result['rmse']:^10.4f} | {result['mae']:^10.4f} | "
                      f"{result['r2']:^10.4f} | {cv_score:^8.4f}±{result['cv_std']:^.3f}")
        else:
            print(f"{'모델':^15} | {'Accuracy':^10} | {'Precision':^10} | {'Recall':^10} | {'F1-Score':^10} | {'CV Score':^15}")
            print("-" * 95)
            
            for name, result in self.results.items():
                print(f"{name:^15} | {result['accuracy']:^10.4f} | {result['precision']:^10.4f} | "
                      f"{result['recall']:^10.4f} | {result['f1']:^10.4f} | "
                      f"{result['cv_mean']:^8.4f}±{result['cv_std']:^.3f}")
    
    def plot_results(self, figsize=(16, 12)):
        """결과 시각화"""
        if not self.results:
            print("⚠️ 평가 결과가 없습니다.")
            return
        
        plt.style.use('seaborn-v0_8')
        
        if self.task == 'regression':
            self._plot_regression_results(figsize)
        else:
            self._plot_classification_results(figsize)
    
    def _plot_regression_results(self, figsize):
        """회귀 결과 시각화"""
        fig, axes = plt.subplots(2, 3, figsize=figsize)
        fig.suptitle(f'🔍 회귀 모델 평가 결과 (타깃: {self.target})', fontsize=16, fontweight='bold')
        
        models = list(self.results.keys())
        
        # 1. 주요 메트릭 비교
        metrics = ['rmse', 'mae', 'r2']
        colors = ['skyblue', 'lightcoral', 'lightgreen']
        
        for i, metric in enumerate(metrics):
            ax = axes[0, i]
            values = [self.results[model][metric] for model in models]
            
            bars = ax.bar(models, values, color=colors[i], alpha=0.7)
            ax.set_title(f'{metric.upper()} 비교')
            ax.set_xlabel('모델')
            ax.set_ylabel(metric.upper())
            plt.setp(ax.get_xticklabels(), rotation=45)
            
            # 값 표시
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                       f'{value:.3f}', ha='center', va='bottom', fontsize=9)
        
        # 2. 교차검증 점수 분포
        ax = axes[1, 0]
        cv_data = [self.results[model]['cv_scores'] for model in models]
        bp = ax.boxplot(cv_data, labels=models, patch_artist=True)
        
        # 박스플롯 색상 설정
        colors_box = plt.cm.Set3(np.linspace(0, 1, len(models)))
        for patch, color in zip(bp['boxes'], colors_box):
            patch.set_facecolor(color)
        
        ax.set_title('교차검증 점수 분포')
        ax.set_xlabel('모델')
        ax.set_ylabel('CV Score')
        plt.setp(ax.get_xticklabels(), rotation=45)
        
        # 3. 실제값 vs 예측값 (최고 성능 모델)
        primary_metric = self.metrics_config['primary']
        if primary_metric == 'r2':
            best_model = max(models, key=lambda x: self.results[x]['r2'])
        else:
            best_model = min(models, key=lambda x: self.results[x][primary_metric])
        
        ax = axes[1, 1]
        y_true = self.results[best_model]['y_true']
        y_pred = self.results[best_model]['y_pred']
        
        ax.scatter(y_true, y_pred, alpha=0.6, color='blue', s=20)
        ax.plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()], 'r--', lw=2)
        ax.set_xlabel('실제값')
        ax.set_ylabel('예측값')
        ax.set_title(f'실제값 vs 예측값 ({best_model})')
        
        # R² 표시
        r2 = self.results[best_model]['r2']
        ax.text(0.05, 0.95, f'R² = {r2:.3f}', transform=ax.transAxes, 
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # 4. 잔차 플롯
        ax = axes[1, 2]
        residuals = y_true - y_pred
        ax.scatter(y_pred, residuals, alpha=0.6, color='green', s=20)
        ax.axhline(y=0, color='r', linestyle='--', linewidth=2)
        ax.set_xlabel('예측값')
        ax.set_ylabel('잔차')
        ax.set_title(f'잔차 플롯 ({best_model})')
        
        plt.tight_layout()
        plt.show()
    
    def _plot_classification_results(self, figsize):
        """분류 결과 시각화"""
        fig, axes = plt.subplots(2, 3, figsize=figsize)
        fig.suptitle(f'🎯 분류 모델 평가 결과 (타깃: {self.target})', fontsize=16, fontweight='bold')
        
        models = list(self.results.keys())
        
        # 1. 메트릭 비교
        metrics = ['accuracy', 'precision', 'recall', 'f1']
        colors = ['skyblue', 'lightcoral', 'lightgreen', 'gold']
        
        ax = axes[0, 0]
        x = np.arange(len(models))
        width = 0.2
        
        for i, metric in enumerate(metrics):
            values = [self.results[model][metric] for model in models]
            bars = ax.bar(x + i*width, values, width, label=metric, color=colors[i], alpha=0.7)
            
            # 값 표시
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                       f'{value:.3f}', ha='center', va='bottom', fontsize=8)
        
        ax.set_xlabel('모델')
        ax.set_ylabel('점수')
        ax.set_title('분류 메트릭 비교')
        ax.set_xticks(x + width * 1.5)
        ax.set_xticklabels(models, rotation=45)
        ax.legend()
        ax.set_ylim(0, 1.1)
        
        # 2. ROC 곡선 (이진분류)
        ax = axes[0, 1]
        has_roc = False
        for model_name in models:
            if 'roc_auc' in self.results[model_name]:
                has_roc = True
                y_true = self.results[model_name]['y_true']
                y_proba = self.results[model_name]['y_proba']
                fpr, tpr, _ = roc_curve(y_true, y_proba)
                auc = self.results[model_name]['roc_auc']
                
                ax.plot(fpr, tpr, label=f'{model_name} (AUC = {auc:.3f})')
        
        if has_roc:
            ax.plot([0, 1], [0, 1], 'k--', label='Random')
            ax.set_xlabel('False Positive Rate')
            ax.set_ylabel('True Positive Rate')
            ax.set_title('ROC 곡선')
            ax.legend()
        else:
            ax.text(0.5, 0.5, 'ROC 곡선\n(이진분류 전용)', ha='center', va='center', transform=ax.transAxes)
        
        # 3. 혼동행렬 (최고 성능 모델)
        best_model = max(models, key=lambda x: self.results[x]['accuracy'])
        ax = axes[0, 2]
        y_true = self.results[best_model]['y_true']
        y_pred = self.results[best_model]['y_pred']
        cm = confusion_matrix(y_true, y_pred)
        
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax)
        ax.set_title(f'혼동행렬 ({best_model})')
        ax.set_xlabel('예측값')
        ax.set_ylabel('실제값')
        
        # 4. 모델별 정확도
        ax = axes[1, 0]
        accuracies = [self.results[model]['accuracy'] for model in models]
        
        bars = ax.bar(models, accuracies, color='lightblue', alpha=0.7)
        ax.set_title('모델별 정확도')
        ax.set_xlabel('모델')
        ax.set_ylabel('정확도')
        plt.setp(ax.get_xticklabels(), rotation=45)
        
        for bar, acc in zip(bars, accuracies):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                   f'{acc:.3f}', ha='center', va='bottom', fontsize=9)
        
        # 5. 특성 중요도 (트리 기반 모델)
        ax = axes[1, 1]
        tree_models = ['rf', 'lgbm', 'xgb', 'cat']
        available_tree_models = [m for m in tree_models if m in models]
        
        if available_tree_models:
            model_name = available_tree_models[0]
            model = self.results[model_name]['model']
            
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
                feature_names = [f'Feature_{i}' for i in range(len(importances))]
                
                indices = np.argsort(importances)[::-1][:10]
                
                ax.barh(range(len(indices)), importances[indices], color='lightgreen', alpha=0.7)
                ax.set_title(f'특성 중요도 ({model_name})')
                ax.set_xlabel('중요도')
                ax.set_yticks(range(len(indices)))
                ax.set_yticklabels([feature_names[i] for i in indices])
        else:
            ax.text(0.5, 0.5, '특성 중요도\n(트리 모델 전용)', ha='center', va='center', transform=ax.transAxes)
        
        # 6. 교차검증 점수
        ax = axes[1, 2]
        cv_data = [self.results[model]['cv_scores'] for model in models]
        bp = ax.boxplot(cv_data, labels=models, patch_artist=True)
        
        colors_box = plt.cm.Set3(np.linspace(0, 1, len(models)))
        for patch, color in zip(bp['boxes'], colors_box):
            patch.set_facecolor(color)
        
        ax.set_title('교차검증 점수 분포')
        ax.set_xlabel('모델')
        ax.set_ylabel('CV Score')
        plt.setp(ax.get_xticklabels(), rotation=45)
        
        plt.tight_layout()
        plt.show()
    
    def get_summary_dataframe(self):
        """결과를 DataFrame으로 반환"""
        if not self.results:
            print("⚠️ 평가 결과가 없습니다.")
            return None
        
        summary_data = []
        for model_name, result in self.results.items():
            if self.task == 'regression': # 회귀 모델델
                row = {
                    '모델': model_name, # 모델 이름
                    'RMSE': result['rmse'], # 예측 오차의 제곱 평균에 루트를 씌운 값. 작을수록 좋음.
                    'MAE': result['mae'], # 예측값과 실제값의 절대 오차 평균. 작을수록 좋음.
                    'R²': result['r2'], # 0~1(또는 음수 가능) 범위로 클수록 좋음. 1이면 완벽한 설명.
                    'CV_Mean': result['cv_mean'], # 교차검증 점수의 평균
                    'CV_Std': result['cv_std'] # 교차검증 점수의 표준편차
                }
            else:  # 분류 모델
                row = {
                    '모델': model_name,
                    'Accuracy': result['accuracy'], # 정확도. 예측값과 실제값이 일치하는 비율. 클수록 좋음.
                    'Precision': result['precision'], # 정밀도. 양성으로 예측한 것 중 실제 양성인 비율. 작을수록 좋음.
                    'Recall': result['recall'], # 재현율. 실제 양성인 것 중 양성으로 예측한 비율. 작을수록 좋음.
                    'F1_Score': result['f1'], # 정밀도와 재현율의 조화평균. 작을수록 좋음.
                    'CV_Mean': result['cv_mean'], # 교차검증 점수의 평균
                    'CV_Std': result['cv_std'] # 교차검증 점수의 표준편차
                }
            summary_data.append(row)
        
        df = pd.DataFrame(summary_data)
        return df.sort_values(by=df.columns[1], ascending=(self.task == 'regression'))
    
    def get_best_model(self):
        """최고 성능 모델 반환"""
        if not self.results:
            return None
        
        if self.task == 'regression':
            primary_metric = self.metrics_config['primary']
            if primary_metric == 'r2':
                best_name = max(self.results.keys(), key=lambda x: self.results[x]['r2'])
            else:
                best_name = min(self.results.keys(), key=lambda x: self.results[x][primary_metric])
        else:
            best_name = max(self.results.keys(), key=lambda x: self.results[x]['accuracy'])
        
        return {
            'name': best_name,
            'model': self.trained_models[best_name],
            'metrics': self.results[best_name]
        }
    
    def finish_wandb(self):
        """wandb 실행 종료"""
        if self.use_wandb:
            wandb.finish()
            print("📊 wandb 실행 종료됨")


if __name__ == "__main__":
    print("모델 평가 도구")
    print("=" * 30)
    print("이미 학습된 모델들을 평가합니다.")
    print()
    print("사용법:")
    print("1. evaluator = ModelEvaluator('config.yaml', use_wandb=True)")
    print("2. evaluator.evaluate_models(pretrained_models, X_test, y_test)")
    print("3. evaluator.plot_results()")
    print("4. evaluator.finish_wandb()")