from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from app.core.schemas import PortfolioSettings

_EPS = np.finfo(float).eps


def _cap_weights(weights: np.ndarray, minimum: float, maximum: float) -> np.ndarray:
    weights = np.maximum(weights, 0.0)
    if float(weights.sum()) <= _EPS:
        weights = np.ones_like(weights)
    weights = weights / weights.sum()
    for _ in range(20):
        previous = weights.copy()
        weights = np.clip(weights, minimum, maximum)
        total = float(weights.sum())
        if total <= _EPS:
            weights = np.ones_like(weights) / len(weights)
        else:
            weights /= total
        if np.max(np.abs(weights - previous)) < 1e-10:
            break
    return weights / weights.sum()


def _risk_parity(covariance: np.ndarray) -> np.ndarray:
    count = covariance.shape[0]
    weights = np.ones(count, dtype=float) / count
    target = 1.0 / count
    for _ in range(500):
        portfolio_variance = float(weights @ covariance @ weights)
        if portfolio_variance <= _EPS:
            return np.ones(count) / count
        marginal = covariance @ weights
        contributions = weights * marginal / portfolio_variance
        adjustment = np.sqrt(np.maximum(target, _EPS) / np.maximum(contributions, _EPS))
        updated = np.maximum(weights * adjustment, _EPS)
        updated /= updated.sum()
        if np.max(np.abs(updated - weights)) < 1e-9:
            weights = updated
            break
        weights = 0.5 * weights + 0.5 * updated
    return weights / weights.sum()


def _allocation_weights(returns: pd.DataFrame, method: str) -> np.ndarray:
    count = returns.shape[1]
    if method == "equal" or len(returns) < 3:
        return np.ones(count) / count
    covariance = returns.cov().to_numpy(dtype=float)
    covariance += np.eye(count) * 1e-10
    if method == "inverse_volatility":
        volatility = np.sqrt(np.maximum(np.diag(covariance), _EPS))
        inverse = 1.0 / volatility
        return inverse / inverse.sum()
    if method == "risk_parity":
        return _risk_parity(covariance)
    if method == "minimum_variance":
        inverse = np.linalg.pinv(covariance)
        ones = np.ones(count)
        raw = inverse @ ones
        return raw / max(float(ones @ inverse @ ones), _EPS)
    raise ValueError(f"Unknown allocation method: {method}")


def _max_drawdown(values: np.ndarray) -> float:
    running = np.maximum.accumulate(values)
    return float(np.min(values / np.maximum(running, _EPS) - 1.0))


def analyse_multi_asset(datasets: dict[str, pd.DataFrame]) -> dict[str, Any]:
    if len(datasets) < 2:
        raise ValueError("Upload at least two assets for multi-asset analysis.")
    closes = pd.concat(
        [df.set_index("timestamp")["close"].rename(name) for name, df in datasets.items()], axis=1, join="inner"
    ).dropna()
    if len(closes) < 20:
        raise ValueError("The uploaded assets do not have at least 20 matching timestamps.")
    returns = np.log(closes).diff().dropna()
    correlation = returns.corr()
    volatility = returns.std(ddof=1) * 100.0
    total_return = (closes.iloc[-1] / closes.iloc[0] - 1.0) * 100.0
    diversification_ratio = float(volatility.mean() / max(float(returns.mean(axis=1).std(ddof=1) * 100.0), _EPS))
    return {
        "assets": list(closes.columns),
        "matched_rows": len(closes),
        "start": pd.Timestamp(closes.index[0]).isoformat(),
        "end": pd.Timestamp(closes.index[-1]).isoformat(),
        "correlation": {
            row: {column: round(float(correlation.loc[row, column]), 5) for column in correlation.columns}
            for row in correlation.index
        },
        "volatility_percent_per_candle": {name: round(float(value), 5) for name, value in volatility.items()},
        "total_return_percent": {name: round(float(value), 4) for name, value in total_return.items()},
        "diversification_ratio_equal_weight": round(diversification_ratio, 4),
    }


def run_portfolio_simulation(
    datasets: dict[str, pd.DataFrame], settings: PortfolioSettings
) -> dict[str, Any]:
    analysis = analyse_multi_asset(datasets)
    closes = pd.concat(
        [df.set_index("timestamp")["close"].rename(name) for name, df in datasets.items()], axis=1, join="inner"
    ).dropna()
    simple_returns = closes.pct_change().dropna()
    if len(simple_returns) <= settings.lookback:
        raise ValueError(f"At least {settings.lookback + 2} matching candles are required.")

    asset_names = list(simple_returns.columns)
    minimum = settings.min_weight_percent / 100.0
    maximum = settings.max_weight_percent / 100.0
    equity = float(settings.initial_capital)
    equity_values = [equity]
    equity_curve = [{"timestamp": pd.Timestamp(simple_returns.index[0]).isoformat(), "equity": round(equity, 4)}]
    weights = np.ones(len(asset_names)) / len(asset_names)
    weights_history: list[dict[str, Any]] = []
    turnover_total = 0.0
    fee_rate = settings.fee_percent / 100.0

    for index in range(settings.lookback, len(simple_returns)):
        if (index - settings.lookback) % settings.rebalance_every == 0:
            history = simple_returns.iloc[index - settings.lookback : index]
            raw = _allocation_weights(history, settings.allocation)
            new_weights = _cap_weights(raw, minimum, maximum)
            turnover = float(np.sum(np.abs(new_weights - weights)))
            equity *= max(0.0, 1.0 - turnover * fee_rate)
            turnover_total += turnover
            weights = new_weights
            weights_history.append(
                {
                    "timestamp": pd.Timestamp(simple_returns.index[index]).isoformat(),
                    "turnover_percent": round(turnover * 100.0, 4),
                    "weights": {asset_names[i]: round(float(weights[i]) * 100.0, 4) for i in range(len(weights))},
                }
            )
        period_return = float(np.dot(weights, simple_returns.iloc[index].to_numpy(dtype=float)))
        if settings.target_volatility_percent is not None:
            history = simple_returns.iloc[max(0, index - settings.lookback) : index]
            portfolio_hist = history.to_numpy(dtype=float) @ weights
            realised = float(np.std(portfolio_hist, ddof=1) * 100.0) if len(portfolio_hist) > 1 else 0.0
            leverage = min(2.0, settings.target_volatility_percent / max(realised, 1e-8))
            period_return *= leverage
        equity *= max(0.0, 1.0 + period_return)
        equity_values.append(equity)
        equity_curve.append(
            {"timestamp": pd.Timestamp(simple_returns.index[index]).isoformat(), "equity": round(equity, 4)}
        )

    values = np.asarray(equity_values, dtype=float)
    portfolio_returns = pd.Series(values).pct_change().dropna().to_numpy(dtype=float)
    mean = float(np.mean(portfolio_returns)) if len(portfolio_returns) else 0.0
    sigma = float(np.std(portfolio_returns, ddof=1)) if len(portfolio_returns) > 1 else 0.0
    downside = portfolio_returns[portfolio_returns < 0]
    downside_sigma = float(np.std(downside, ddof=1)) if len(downside) > 1 else 0.0

    metrics = {
        "initial_capital": round(settings.initial_capital, 2),
        "final_equity": round(equity, 2),
        "total_return_percent": round((equity / settings.initial_capital - 1.0) * 100.0, 4),
        "max_drawdown_percent": round(_max_drawdown(values) * 100.0, 4),
        "mean_return_percent_per_candle": round(mean * 100.0, 6),
        "volatility_percent_per_candle": round(sigma * 100.0, 6),
        "sharpe_per_sqrt_candle": round(mean / sigma, 5) if sigma > 0 else 0.0,
        "sortino_per_sqrt_candle": round(mean / downside_sigma, 5) if downside_sigma > 0 else 0.0,
        "total_turnover_percent": round(turnover_total * 100.0, 4),
        "rebalances": len(weights_history),
    }
    return {
        "metrics": metrics,
        "analysis": analysis,
        "settings": settings.model_dump(),
        "latest_weights": weights_history[-1]["weights"] if weights_history else {
            asset_names[i]: round(float(weights[i]) * 100.0, 4) for i in range(len(weights))
        },
        "weights_history": weights_history[-500:],
        "equity_curve": equity_curve[-5000:],
        "notes": [
            "Assets are aligned on matching timestamps only.",
            "Allocation weights use trailing data and are applied after the rebalance decision.",
            "This simulation does not model taxes, borrow costs, funding, market impact or partial fills.",
        ],
    }
