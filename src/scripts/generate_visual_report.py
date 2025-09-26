"""CLI entrypoint for generating commute weather EDA and visual reports."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.data.weather_processor import WeatherDataProcessor
from src.utils.config import KMAApiConfig, S3Config
from src.visualization import WeatherVisualizationReport
from src.eda import build_overall_profile, build_station_profile, run_data_quality_checks
from src.utils.logger_config import configure_logger


_logger = configure_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate commute weather EDA and visualisations")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/visualizations/reports"),
        help="Directory where generated plots will be stored",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="How many days back to search for the latest ML dataset",
    )
    parser.add_argument(
        "--station",
        type=str,
        default=None,
        help="Optional station id to focus on a single location",
    )
    return parser.parse_args()


def run(output_dir: Path, days_back: int, station: str | None) -> None:
    """Load dataset from S3, run EDA checks, and generate plots."""
    kma_config = KMAApiConfig.from_env()
    s3_config = S3Config.from_env()

    processor = WeatherDataProcessor(kma_config=kma_config, s3_config=s3_config)
    dataset = processor.load_latest_ml_dataset(days_back=days_back)
    if dataset is None or dataset.empty:
        raise RuntimeError("No ML dataset found in the configured S3 bucket")

    # Run EDA diagnostics
    profile = build_overall_profile(dataset)
    station_profile = build_station_profile(dataset, station_id=station)
    quality_issues = run_data_quality_checks(dataset)

    _logger.info("Overall profile computed", extra={"summary_rows": len(profile["summary"])})
    _logger.info("Station profile computed", extra={"station": station})
    if any(quality_issues.values()):
        _logger.warning("Data quality issues detected", extra=quality_issues)

    # Save tabular outputs alongside plots
    report_dir = Path(output_dir)
    report_dir.mkdir(parents=True, exist_ok=True)

    profile["summary"].to_csv(report_dir / "summary.csv")
    profile["missing"].to_csv(report_dir / "missingness.csv")
    profile["daily_coverage"].to_csv(report_dir / "daily_coverage.csv")
    station_profile["percentiles"].to_csv(report_dir / "station_percentiles.csv")
    station_profile["comfort_score"].to_csv(report_dir / "station_comfort.csv")

    vis_report = WeatherVisualizationReport(report_dir)
    vis_report.build(dataset, station_ids=[station] if station else None)

    _logger.info("Report generation completed", extra={"output": str(report_dir)})


def main() -> None:
    args = parse_args()
    run(args.output, args.days, args.station)


if __name__ == "__main__":
    main()
