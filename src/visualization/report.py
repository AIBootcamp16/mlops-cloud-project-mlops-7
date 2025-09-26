"""Composite visualization workflows for commute weather data."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Optional

import matplotlib.pyplot as plt
import pandas as pd

from src.visualization.plotting import (
    plot_comfort_score_timeseries,
    plot_pm10_distribution,
    plot_temperature_trend,
    plot_uv_intensity,
)
from src.utils.logger_config import configure_logger


_logger = configure_logger(__name__)


class WeatherVisualizationReport:
    """Generate and persist a standard set of visualisations for stakeholders."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        _logger.info("Visualization output directory prepared", extra={"path": str(self.output_dir)})

    def build(self, df: pd.DataFrame, station_ids: Optional[Iterable[str]] = None) -> Dict[str, Path]:
        """Create plots for each station and return the generated file paths."""
        results: Dict[str, Path] = {}
        if station_ids:
            targets = [str(s) for s in station_ids]
        else:
            targets = ["all"]

        for station in targets:
            station_suffix = station if station != "all" else "aggregate"
            if station == "all" or "station_id" not in df.columns:
                sub_df = df
            else:
                sub_df = df[df["station_id"].astype(str) == str(station)]

            plotters = (
                ("temperature", plot_temperature_trend),
                ("pm10", plot_pm10_distribution),
                ("uv", plot_uv_intensity),
                ("comfort", plot_comfort_score_timeseries),
            )

            generated = 0
            skipped = []
            for metric_name, plotter in plotters:
                try:
                    figure = plotter(sub_df, station_id=None if station == "all" else station)
                except ValueError as exc:
                    skipped.append((metric_name, str(exc)))
                    continue

                filename = f"{metric_name}_{station_suffix}.png"
                target_path = self.output_dir / filename
                figure.savefig(target_path, dpi=150)
                plt.close(figure)
                results[f"{station_suffix}:{filename}"] = target_path
                generated += 1

            if generated:
                _logger.info("Visualization set saved", extra={"station_id": station_suffix, "count": generated})
            if skipped:
                _logger.warning("Visualizations skipped", extra={"station_id": station_suffix, "metrics": skipped})

        return results


__all__ = ["WeatherVisualizationReport"]
