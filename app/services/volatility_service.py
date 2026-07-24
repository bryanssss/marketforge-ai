from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.core.schemas import VolatilitySettings

_EPS = np.finfo(float).eps


def _ewma_variance(returns: np.ndarray, decay: float) -> float:
    variance = float(np.var(returns, ddof=1)) if len(returns) > 1 else 0.0
    for value in returns:
        variance = decay * variance + (1.0 - decay) * float(value * value)
    return max(variance, 0.0)


def _parkinson_variance(df: pd.DataFrame) -> float:
    values = np.log(np.maximum(df["high"].to_numpy(dtype=float), _EPS) / np.maximum(df["low"].to_numpy(dtype=float), _EPS))
    return float(np.mean(values**2) / (4.0 * np.log(2.0)))


def _garman_klass_variance(df: pd.DataFrame) -> float:
    high_low = np.log(np.maximum(df["high"].to_numpy(dtype=float), _EPS) / np.maximum(df["low"].to_numpy(dtype=float), _EPS))
    close_open = np.log(np.maximum(df["close"].to_numpy(dtype=float), _EPS) / np.maximum(df["open"].to_numpy(dtype=float), _EPS))
    variance = 0.5 * high_low**2 - (2.0 * np.log(2.0) - 1.0) * close_open**2
    return max(float(np.mean(variance)), 0.0)


def forecast_volatility(df: pd.DataFrame, settings: VolatilitySettings) -> dict[str, Any]:
    if len(df) < settings.lookback:
        raise ValueError(f"At least {settings.lookback} candles are required.")
    window = df.tail(settings.lookback)
    returns = np.diff(np.log(np.maximum(window["close"].to_numpy(dtype=float), _EPS)))
    if len(returns) < 2:
        raise ValueError("Not enough price changes to forecast volatility.")

    estimates = {
        "ewma": _ewma_variance(returns, settings.decay),
        "parkinson": _parkinson_variance(window),
        "garman_klass": _garman_klass_variance(window),
    }
    variance = float(np.mean(list(estimates.values()))) if settings.method == "ensemble" else estimates[settings.method]
    per_candle = float(np.sqrt(max(variance, 0.0)))
    horizon_vol = per_candle * np.sqrt(settings.horizon)
    annualised = per_candle * np.sqrt(settings.annualisation_periods)

    rolling = pd.Series(returns).rolling(min(24, len(returns))).std().dropna()
    if rolling.empty:
        lower = per_candle * 0.75
        upper = per_candle * 1.25
    else:
        lower = float(rolling.quantile(0.10))
        upper = float(rolling.quantile(0.90))

    return {
        "method": settings.method,
        "lookback": settings.lookback,
        "horizon": settings.horizon,
        "per_candle_volatility_percent": round(per_candle * 100.0, 5),
        "horizon_volatility_percent": round(horizon_vol * 100.0, 5),
        "annualised_volatility_percent": round(annualised * 100.0, 3),
        "historical_10_90_range_percent": [round(lower * 100.0, 5), round(upper * 100.0, 5)],
        "component_estimates_percent": {
            key: round(float(np.sqrt(max(value, 0.0))) * 100.0, 5) for key, value in estimates.items()
        },
        "notes": [
            "Volatility forecasts estimate dispersion, not price direction.",
            "Annualisation depends on the supplied periods-per-year setting and the candle timeframe.",
        ],
    }
