"""Data profiling helpers for commute weather datasets."""
from __future__ import annotations

from typing import Dict, Optional

import pandas as pd


def _prepare(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    if "datetime" in cleaned.columns:
        cleaned["datetime"] = pd.to_datetime(cleaned["datetime"], utc=True, errors="coerce")
    return cleaned


def build_overall_profile(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Return summary statistics, missingness, and time coverage tables."""
    data = _prepare(df)
    summary = data.describe(include="all").transpose()
    missing = data.isna().mean().mul(100).rename("missing_pct").to_frame()

    coverage = pd.DataFrame()
    if "datetime" in data.columns:
        coverage = data.groupby(data["datetime"].dt.date).size().rename("records").to_frame()

    return {
        "summary": summary,
        "missing": missing,
        "daily_coverage": coverage,
    }


def build_station_profile(df: pd.DataFrame, station_id: Optional[str] = None) -> Dict[str, pd.DataFrame]:
    """Provide station-level profile including comfort score distribution."""
    data = _prepare(df)
    if station_id is not None:
        data = data[data["station_id"].astype(str) == str(station_id)]

    numeric = data.select_dtypes(include=["number"])
    if numeric.empty:
        percentiles = pd.DataFrame()
    else:
        percentiles = numeric.quantile([0.05, 0.25, 0.5, 0.75, 0.95]).transpose()

    comfort = pd.Series(dtype=float)
    if "comfort_score" in data.columns:
        comfort = pd.to_numeric(data["comfort_score"], errors="coerce").dropna()

    comfort_stats = pd.DataFrame({
        "mean": [comfort.mean()],
        "std": [comfort.std()],
        "min": [comfort.min()],
        "max": [comfort.max()],
        "count": [comfort.count()],
    })

    return {
        "percentiles": percentiles,
        "comfort_score": comfort_stats,
    }


__all__ = ["build_overall_profile", "build_station_profile"]
