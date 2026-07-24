from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

_EPS = np.finfo(float).eps


def calibrate_forecast_intervals(
    context: pd.DataFrame,
    forecast: pd.DataFrame,
    method: str,
    level: float,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    if method == "none":
        return forecast, {"method": "none", "level": level, "observations": 0}

    closes = np.maximum(context["close"].to_numpy(dtype=float), _EPS)
    returns = np.diff(np.log(closes))
    if len(returns) < 20:
        return forecast, {
            "method": method,
            "level": level,
            "observations": len(returns),
            "warning": "Not enough residual history; original model intervals were retained.",
        }

    if method == "conformal":
        series = pd.Series(returns)
        predicted = series.shift(1).rolling(min(20, len(series) // 2)).median()
        residuals = (series - predicted).dropna().abs().to_numpy(dtype=float)
        if not len(residuals):
            residuals = np.abs(returns - np.median(returns))
    else:
        residuals = np.abs(returns - np.median(returns))

    quantile = float(np.quantile(residuals, min(max(level, 0.5), 0.99)))
    output = forecast.copy()
    original_lower = output["lower_close"].to_numpy(dtype=float)
    original_upper = output["upper_close"].to_numpy(dtype=float)
    centre = np.maximum(output["close"].to_numpy(dtype=float), _EPS)
    steps = np.sqrt(np.arange(1, len(output) + 1, dtype=float))
    empirical_lower = centre * np.exp(-quantile * steps)
    empirical_upper = centre * np.exp(quantile * steps)

    if method == "conformal":
        output["lower_close"] = np.minimum(original_lower, empirical_lower)
        output["upper_close"] = np.maximum(original_upper, empirical_upper)
    else:
        original_radius = 0.5 * (
            np.log(np.maximum(original_upper, _EPS)) - np.log(np.maximum(original_lower, _EPS))
        )
        empirical_radius = quantile * steps
        blended = 0.5 * original_radius + 0.5 * empirical_radius
        output["lower_close"] = centre * np.exp(-blended)
        output["upper_close"] = centre * np.exp(blended)

    return output, {
        "method": method,
        "level": level,
        "observations": len(residuals),
        "absolute_log_residual_quantile": round(quantile, 8),
        "rule": "widen-only conformal" if method == "conformal" else "model/empirical radius blend",
    }
