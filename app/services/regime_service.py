from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def classify_market_regime(df: pd.DataFrame, lookback: int = 120) -> dict[str, Any]:
    if len(df) < 20:
        raise ValueError("At least 20 candles are required for regime classification.")
    window = df.tail(min(lookback, len(df))).copy()
    closes = window["close"].to_numpy(dtype=float)
    returns = np.diff(np.log(np.maximum(closes, np.finfo(float).eps)))
    if not len(returns):
        raise ValueError("Not enough price changes for regime classification.")

    short_span = min(20, max(3, len(closes) // 5))
    long_span = min(60, max(short_span + 1, len(closes) // 2))
    series = pd.Series(closes)
    ema_short = float(series.ewm(span=short_span, adjust=False).mean().iloc[-1])
    ema_long = float(series.ewm(span=long_span, adjust=False).mean().iloc[-1])
    trend_strength = (ema_short / max(ema_long, np.finfo(float).eps) - 1.0) * 100.0

    recent_vol = float(np.std(returns[-min(24, len(returns)) :], ddof=1)) if len(returns) > 1 else 0.0
    rolling_vol = pd.Series(returns).rolling(min(24, len(returns))).std().dropna()
    if rolling_vol.empty:
        volatility_percentile = 50.0
    else:
        volatility_percentile = float((rolling_vol <= recent_vol).mean() * 100.0)

    recent_return = float(np.sum(returns[-min(24, len(returns)) :]) * 100.0)
    downside = returns[returns < 0]
    upside = returns[returns > 0]
    downside_vol = float(np.std(downside, ddof=1)) if len(downside) > 1 else 0.0
    upside_vol = float(np.std(upside, ddof=1)) if len(upside) > 1 else 0.0
    asymmetry = downside_vol / max(upside_vol, np.finfo(float).eps)

    high_vol = volatility_percentile >= 75
    low_vol = volatility_percentile <= 25
    if abs(trend_strength) < 0.35 and abs(recent_return) < 1.0:
        regime = "sideways_low_volatility" if low_vol else "sideways"
    elif trend_strength >= 0.35:
        regime = "uptrend_high_volatility" if high_vol else "uptrend"
    else:
        regime = "downtrend_high_volatility" if high_vol else "downtrend"

    if high_vol and abs(recent_return) >= 8.0:
        regime = "liquidity_shock"

    confidence = min(0.99, 0.45 + min(abs(trend_strength) / 5.0, 0.30) + min(abs(recent_return) / 30.0, 0.20))
    return {
        "regime": regime,
        "confidence": round(float(confidence), 3),
        "trend_strength_percent": round(trend_strength, 4),
        "recent_return_percent": round(recent_return, 4),
        "recent_volatility_percent_per_candle": round(recent_vol * 100.0, 4),
        "volatility_percentile": round(volatility_percentile, 2),
        "downside_upside_volatility_ratio": round(asymmetry, 4),
        "lookback": len(window),
        "notes": [
            "Regimes are descriptive summaries, not trading signals.",
            "Thresholds are transparent heuristics and should be validated on the intended market and timeframe.",
        ],
    }
