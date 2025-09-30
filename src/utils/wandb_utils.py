import wandb


def get_runs(entity, project):
    """WANDB 프로젝트의 모든 실행 조회"""
    return wandb.Api().runs(path=f"{entity}/{project}", order="-created_at")


def get_latest_run_name(entity, project, prefix="weather-predictor"):
    """최신 실험명 조회"""
    runs = get_runs(entity, project)
    matching_runs = [run.name for run in runs if run.name.startswith(prefix)]
    if not matching_runs:
        return f"{prefix}-000"
    return matching_runs[0]


def get_requirements():
    """requirements.txt 파일 읽기"""
    try:
        with open('/app/requirements.txt', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "requirements.txt not found"