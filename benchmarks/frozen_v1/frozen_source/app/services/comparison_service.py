from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.core.config import SETTINGS
from app.core.schemas import BacktestSettings, ComparisonSettings
from app.services.backtest_service import run_walk_forward_backtest

_METRIC_KEYS = (
    "mae_percent",
    "rmse_percent",
    "directional_accuracy_percent",
    "interval_80_coverage_percent",
    "average_interval_width_percent",
)


def compare_baselines(df: pd.DataFrame, settings: ComparisonSettings) -> dict[str, Any]:
    """Compare transparent models on matched rolling-origin dates and repeat seeds."""
    forecast_horizon = settings.horizon
    end_limit = len(df) - forecast_horizon
    evaluations_per_run = len(range(settings.lookback, end_limit, settings.step))
    total_evaluations = evaluations_per_run * len(settings.models) * settings.repeats
    if total_evaluations > SETTINGS.max_comparison_evaluations:
        raise ValueError(
            f"This comparison would run {total_evaluations:,} forecasts. Increase the step, "
            f"reduce repeats/models or use fewer rows. Maximum: {SETTINGS.max_comparison_evaluations:,}."
        )

    rows: list[dict[str, Any]] = []
    for model in settings.models:
        repeated: list[dict[str, Any]] = []
        for repeat in range(settings.repeats):
            result = run_walk_forward_backtest(
                df,
                BacktestSettings(
                    baseline_model=model,
                    horizon=settings.horizon,
                    lookback=settings.lookback,
                    step=settings.step,
                    paths=settings.paths,
                    block_size=settings.block_size,
                    threshold_percent=25.0,
                    direction="long_only",
                    allow_overlap=False,
                    fee_percent=0.0,
                    slippage_percent=0.0,
                    seed=settings.seed + repeat * 10_000,
                ),
            )
            repeated.append(result["forecast_metrics"])

        row: dict[str, Any] = {
            "model": model,
            "evaluations": int(sum(int(item["evaluations"]) for item in repeated)),
            "repeats": settings.repeats,
        }
        for key in _METRIC_KEYS:
            values = np.asarray([float(item[key]) for item in repeated], dtype=float)
            row[key] = round(float(values.mean()), 4)
            row[f"{key}_std"] = round(float(values.std(ddof=1)), 4) if len(values) > 1 else 0.0
        rows.append(row)

    naive = next((row for row in rows if row["model"] == "naive"), None)
    naive_mae = float(naive["mae_percent"]) if naive else 0.0
    for row in rows:
        mae = float(row["mae_percent"])
        row["mae_skill_vs_naive_percent"] = (
            round((naive_mae - mae) / naive_mae * 100.0, 3) if naive_mae > 0 else None
        )
        row["coverage_error_points"] = round(
            abs(float(row["interval_80_coverage_percent"]) - 80.0), 3
        )

    ranking = sorted(
        rows,
        key=lambda row: (
            float(row["mae_percent"]),
            float(row["coverage_error_points"]),
            -float(row["directional_accuracy_percent"]),
        ),
    )
    for rank, row in enumerate(ranking, start=1):
        row["rank"] = rank

    return {
        "ranking": ranking,
        "settings": settings.model_dump(),
        "total_forecasts": total_evaluations,
        "selection_rule": (
            "Ranked by mean MAE across repeat seeds, then interval calibration error, then directional accuracy. "
            "This is descriptive evidence, not proof of future profitability."
        ),
        "notes": [
            "Every model receives the same chronological evaluation dates, history length and repeat seeds.",
            "Repeated stochastic runs reduce the chance that one lucky seed determines the ranking.",
            "The naive model is included as a minimum benchmark; complexity should earn its place.",
            "Coverage near 80% is preferable for an advertised central 80% interval, but width also matters.",
            "Select a model on one period and verify it again on a later untouched period before relying on it.",
        ],
    }
