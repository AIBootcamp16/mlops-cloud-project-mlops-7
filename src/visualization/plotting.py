"""Reusable plotting primitives for commute weather analytics."""
from __future__ import annotations

from datetime import datetime
from typing import Iterable, Optional

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.utils.logger_config import configure_logger


_logger = configure_logger(__name__)


def _validate_dataframe(df: pd.DataFrame, required_columns: Iterable[str]) -> pd.DataFrame:
    """Ensure required columns exist and return a copy with datetime index."""
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"DataFrame missing required columns: {missing}")

    cleaned = df.copy()
    if "datetime" in cleaned.columns:
        cleaned["datetime"] = pd.to_datetime(cleaned["datetime"], utc=True, errors="coerce")
        cleaned = cleaned.dropna(subset=["datetime"])  # drop rows without timestamp
    return cleaned


def plot_temperature_trend(
    df: pd.DataFrame,
    station_id: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
) -> plt.Figure:
    """Plot hourly temperature trend for the given station."""
    required = ["datetime", "temperature"]
    data = _validate_dataframe(df, required)

    if station_id:
        data = data[data["station_id"].astype(str) == str(station_id)]
        _logger.info("Filtered dataframe for station_id", extra={"station_id": station_id, "rows": len(data)})

    if since:
        data = data[data["datetime"] >= pd.Timestamp(since, tz="UTC")]
    if until:
        data = data[data["datetime"] <= pd.Timestamp(until, tz="UTC")]

    if data.empty:
        raise ValueError("No temperature data available for the requested filters")

    plt.figure(figsize=(12, 4))
    sns.lineplot(data=data.sort_values("datetime"), x="datetime", y="temperature", marker="o")
    plt.title("Hourly Temperature Trend")
    plt.xlabel("Datetime (UTC)")
    plt.ylabel("Temperature (°C)")
    plt.grid(True, linestyle="--", alpha=0.3)
    plt.tight_layout()

    fig = plt.gcf()
    return fig


def plot_pm10_distribution(
    df: pd.DataFrame,
    station_id: Optional[str] = None,
    bins: int = 20,
) -> plt.Figure:
    """Plot PM10 distribution for the selected station."""
    required = ["datetime", "pm10"]
    data = _validate_dataframe(df, required)

    if station_id:
        data = data[data["station_id"].astype(str) == str(station_id)]

    # drop missing or non-positive values for distribution
    data = data.dropna(subset=["pm10"])
    if data.empty:
        raise ValueError("No PM10 data available for the requested filters")

    plt.figure(figsize=(8, 4))
    sns.histplot(data["pm10"], bins=bins, kde=True, color="#1f77b4")
    plt.title("PM10 Distribution")
    plt.xlabel("PM10 (µg/m³)")
    plt.ylabel("Frequency")
    plt.tight_layout()

    return plt.gcf()


def plot_uv_intensity(
    df: pd.DataFrame,
    station_id: Optional[str] = None,
    metric: str = "uv_uvb",
) -> plt.Figure:
    """Plot UV intensity over time for the selected UV metric."""
    required = ["datetime", metric]
    data = _validate_dataframe(df, required)

    if station_id:
        data = data[data["station_id"].astype(str) == str(station_id)]

    data = data.dropna(subset=[metric])
    if data.empty:
        raise ValueError("No UV data available for the requested filters")

    plt.figure(figsize=(12, 4))
    sns.lineplot(data=data.sort_values("datetime"), x="datetime", y=metric, marker="o", color="#ff7f0e")
    plt.title(f"UV Intensity Trend ({metric})")
    plt.xlabel("Datetime (UTC)")
    plt.ylabel("Intensity (W/m²)")
    plt.grid(True, linestyle="--", alpha=0.3)
    plt.tight_layout()

    return plt.gcf()


def plot_comfort_score_timeseries(
    df: pd.DataFrame,
    station_id: Optional[str] = None,
) -> plt.Figure:
    """Plot commute comfort score time-series."""
    required = ["datetime", "comfort_score"]
    data = _validate_dataframe(df, required)

    if station_id:
        data = data[data["station_id"].astype(str) == str(station_id)]

    data = data.sort_values("datetime")
    plt.figure(figsize=(12, 4))
    sns.lineplot(data=data, x="datetime", y="comfort_score", marker="o", color="#2ca02c")
    plt.title("Commute Comfort Score Over Time")
    plt.xlabel("Datetime (UTC)")
    plt.ylabel("Comfort Score (0-100)")
    plt.ylim(0, 100)
    plt.grid(True, linestyle="--", alpha=0.3)
    plt.tight_layout()

    return plt.gcf()


__all__ = [
    "plot_temperature_trend",
    "plot_pm10_distribution",
    "plot_uv_intensity",
    "plot_comfort_score_timeseries",
]
