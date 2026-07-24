from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.core.schemas import StressSettings


def run_stress_test(df: pd.DataFrame, settings: StressSettings) -> dict[str, Any]:
    if len(df) < 40:
        raise ValueError("At least 40 candles are required for stress testing.")
    returns = np.diff(np.log(df["close"].to_numpy(dtype=float)))
    recent = returns[-min(250, len(returns)) :]
    mean = float(np.mean(recent))
    sigma = float(np.std(recent, ddof=1)) if len(recent) > 1 else 0.0
    stressed_mean = mean + np.log1p(settings.price_shock_percent / 100.0)
    stressed_sigma = max(sigma * settings.volatility_multiplier, 1e-8)

    rng = np.random.default_rng(settings.seed)
    simulated = rng.normal(stressed_mean, stressed_sigma, settings.scenarios)
    liquidity_cost = settings.liquidity_cost_percent / 100.0
    net = np.expm1(simulated) - liquidity_cost
    percentiles = np.quantile(net, [0.01, 0.05, 0.50, 0.95, 0.99]) * 100.0
    losses = -net[net < 0]

    return {
        "settings": settings.model_dump(),
        "scenarios": settings.scenarios,
        "loss_probability_percent": round(float((net < 0).mean() * 100.0), 3),
        "expected_stressed_return_percent": round(float(np.mean(net) * 100.0), 4),
        "value_at_risk_95_percent": round(float(-np.quantile(net, 0.05) * 100.0), 4),
        "expected_shortfall_95_percent": round(
            float(np.mean(-net[net <= np.quantile(net, 0.05)]) * 100.0), 4
        ),
        "average_loss_percent": round(float(np.mean(losses) * 100.0), 4) if len(losses) else 0.0,
        "return_percentiles": {
            "p01": round(float(percentiles[0]), 4),
            "p05": round(float(percentiles[1]), 4),
            "p50": round(float(percentiles[2]), 4),
            "p95": round(float(percentiles[3]), 4),
            "p99": round(float(percentiles[4]), 4),
        },
        "notes": [
            "This is a transparent scenario simulation, not a prediction of a specific crisis.",
            "The price shock is applied as an immediate log-return shift and liquidity cost is deducted from every scenario.",
        ],
    }
