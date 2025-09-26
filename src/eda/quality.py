"""Data quality checks for commute weather datasets."""
from __future__ import annotations

from typing import Dict, List

import pandas as pd


def run_data_quality_checks(df: pd.DataFrame) -> Dict[str, List[str]]:
    """Evaluate simple data quality rules and return failing messages."""
    issues: Dict[str, List[str]] = {
        "critical": [],
        "warning": [],
    }

    if df.empty:
        issues["critical"].append("Dataset is empty")
        return issues

    if "datetime" not in df.columns:
        issues["critical"].append("Missing datetime column")
    else:
        # datetime monotonicity check per station
        grouped = df.sort_values("datetime").groupby(df.get("station_id", pd.Series()))
        for station, station_df in grouped:
            if station_df["datetime"].is_monotonic_increasing is False:
                issues["warning"].append(f"Datetime not sorted for station {station}")

    if "temperature" in df.columns:
        out_of_range = df[(df["temperature"] < -60) | (df["temperature"] > 60)]
        if not out_of_range.empty:
            issues["warning"].append("Temperature values outside expected range (-60, 60)")

    if "pm10" in df.columns:
        negative_pm10 = df[df["pm10"] < 0]
        if not negative_pm10.empty:
            issues["warning"].append("Negative PM10 readings detected")

    if "comfort_score" in df.columns:
        invalid_comfort = df[(df["comfort_score"] < 0) | (df["comfort_score"] > 100)]
        if not invalid_comfort.empty:
            issues["critical"].append("Comfort score outside 0-100 range")

    return issues


__all__ = ["run_data_quality_checks"]
