from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from app.core.config import SETTINGS
from app.core.errors import ForecastError
from app.core.schemas import BacktestSettings, ForecastSettings
from app.services.forecast_service import baseline_forecast


@dataclass(frozen=True)
class ExitResolution:
    index: int
    price: float
    reason: str


def _max_drawdown(equity: list[float]) -> float:
    if not equity:
        return 0.0
    values = np.asarray(equity, dtype=float)
    running_max = np.maximum.accumulate(values)
    safe_max = np.maximum(running_max, np.finfo(float).eps)
    drawdowns = values / safe_max - 1.0
    return float(drawdowns.min())


def _round_timestamp(value: object) -> str:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    return timestamp.isoformat().replace("+00:00", "Z")


def _resolve_exit(
    df: pd.DataFrame,
    entry_index: int,
    planned_exit_index: int,
    entry_price: float,
    side: int,
    stop_loss_percent: float | None,
    take_profit_percent: float | None,
) -> ExitResolution:
    stop = None
    target = None
    if stop_loss_percent is not None:
        stop = entry_price * (1.0 - stop_loss_percent / 100.0) if side == 1 else entry_price * (
            1.0 + stop_loss_percent / 100.0
        )
    if take_profit_percent is not None:
        target = entry_price * (1.0 + take_profit_percent / 100.0) if side == 1 else entry_price * (
            1.0 - take_profit_percent / 100.0
        )

    for index in range(entry_index, planned_exit_index + 1):
        bar = df.iloc[index]
        open_price = float(bar["open"])
        high = float(bar["high"])
        low = float(bar["low"])

        if side == 1:
            if stop is not None and open_price <= stop:
                return ExitResolution(index, open_price, "stop_gap")
            if target is not None and open_price >= target:
                return ExitResolution(index, open_price, "target_gap")
            stop_hit = stop is not None and low <= stop
            target_hit = target is not None and high >= target
        else:
            if stop is not None and open_price >= stop:
                return ExitResolution(index, open_price, "stop_gap")
            if target is not None and open_price <= target:
                return ExitResolution(index, open_price, "target_gap")
            stop_hit = stop is not None and high >= stop
            target_hit = target is not None and low <= target

        if stop_hit and target_hit:
            return ExitResolution(index, float(stop), "stop_same_bar_conservative")
        if stop_hit:
            return ExitResolution(index, float(stop), "stop")
        if target_hit:
            return ExitResolution(index, float(target), "target")

    return ExitResolution(planned_exit_index, float(df["close"].iloc[planned_exit_index]), "time")


def _net_trade_return(entry: float, exit_price: float, side: int, cost_rate: float) -> float:
    if side == 1:
        cash_out = entry * (1.0 + cost_rate)
        cash_in = exit_price * (1.0 - cost_rate)
        return cash_in / cash_out - 1.0
    sale_proceeds = entry * (1.0 - cost_rate)
    buyback_cost = exit_price * (1.0 + cost_rate)
    return (sale_proceeds - buyback_cost) / entry


def _profit_factor(returns: np.ndarray) -> float:
    wins = returns[returns > 0]
    losses = returns[returns < 0]
    if not len(losses) or float(losses.sum()) == 0:
        return math.inf if len(wins) else 0.0
    return float(wins.sum() / abs(losses.sum()))




def _longest_streak(values: np.ndarray, positive: bool) -> int:
    longest = 0
    current = 0
    for value in values:
        matched = value > 0 if positive else value < 0
        current = current + 1 if matched else 0
        longest = max(longest, current)
    return longest


def _expanded_diagnostics(returns: np.ndarray, equity_values: list[float]) -> dict[str, float | int]:
    if not len(returns):
        return {
            "trade_var_95_percent": 0.0,
            "trade_expected_shortfall_95_percent": 0.0,
            "ulcer_index_percent": 0.0,
            "recovery_factor": 0.0,
            "omega_ratio": 0.0,
            "return_skewness": 0.0,
            "return_excess_kurtosis": 0.0,
            "longest_win_streak": 0,
            "longest_loss_streak": 0,
        }
    values = np.asarray(equity_values, dtype=float)
    running = np.maximum.accumulate(values)
    drawdowns = values / np.maximum(running, np.finfo(float).eps) - 1.0
    ulcer = float(np.sqrt(np.mean(drawdowns**2)))
    max_dd = abs(float(drawdowns.min()))
    total_return = float(values[-1] / max(values[0], np.finfo(float).eps) - 1.0)
    threshold = 0.0
    gains = float(np.sum(np.maximum(returns - threshold, 0.0)))
    losses = float(np.sum(np.maximum(threshold - returns, 0.0)))
    mean = float(np.mean(returns))
    standard = float(np.std(returns, ddof=1)) if len(returns) > 1 else 0.0
    if standard > 0:
        centred = (returns - mean) / standard
        skew = float(np.mean(centred**3))
        kurtosis = float(np.mean(centred**4) - 3.0)
    else:
        skew = 0.0
        kurtosis = 0.0
    quantile = float(np.quantile(returns, 0.05))
    tail = returns[returns <= quantile]
    return {
        "trade_var_95_percent": round(-quantile * 100.0, 4),
        "trade_expected_shortfall_95_percent": round(float(-np.mean(tail) * 100.0), 4),
        "ulcer_index_percent": round(ulcer * 100.0, 4),
        "recovery_factor": round(total_return / max_dd, 4) if max_dd > 0 else 0.0,
        "omega_ratio": round(gains / losses, 4) if losses > 0 else 0.0,
        "return_skewness": round(skew, 4),
        "return_excess_kurtosis": round(kurtosis, 4),
        "longest_win_streak": _longest_streak(returns, True),
        "longest_loss_streak": _longest_streak(returns, False),
    }

def _forecast_metrics(records: list[dict[str, float]]) -> dict[str, float | int]:
    if not records:
        return {
            "evaluations": 0,
            "mae_percent": 0.0,
            "rmse_percent": 0.0,
            "directional_accuracy_percent": 0.0,
            "interval_80_coverage_percent": 0.0,
            "average_interval_width_percent": 0.0,
        }

    errors = np.asarray([row["error_percent"] for row in records], dtype=float)
    correct = np.asarray([row["direction_correct"] for row in records], dtype=float)
    covered = np.asarray([row["covered"] for row in records], dtype=float)
    widths = np.asarray([row["interval_width_percent"] for row in records], dtype=float)
    return {
        "evaluations": len(records),
        "mae_percent": round(float(np.mean(np.abs(errors))), 4),
        "rmse_percent": round(float(np.sqrt(np.mean(errors**2))), 4),
        "directional_accuracy_percent": round(float(np.mean(correct) * 100), 2),
        "interval_80_coverage_percent": round(float(np.mean(covered) * 100), 2),
        "average_interval_width_percent": round(float(np.mean(widths)), 4),
    }


def run_walk_forward_backtest(df: pd.DataFrame, settings: BacktestSettings) -> dict[str, Any]:
    forecast_horizon = settings.execution_delay - 1 + settings.horizon
    minimum = settings.lookback + forecast_horizon + 1
    if len(df) < minimum:
        raise ValueError(f"Backtesting needs at least {minimum} candles for these settings.")

    end_limit = len(df) - forecast_horizon
    possible_evaluations = len(range(settings.lookback, end_limit, settings.step))
    if possible_evaluations > SETTINGS.max_backtest_evaluations:
        recommended_step = math.ceil(
            (end_limit - settings.lookback) / SETTINGS.max_backtest_evaluations
        )
        raise ValueError(
            f"This configuration would run {possible_evaluations:,} forecasts. Increase the step to at least "
            f"{recommended_step} or use fewer rows."
        )

    trades: list[dict[str, Any]] = []
    forecast_records: list[dict[str, float]] = []
    equity = 1.0
    equity_values = [equity]
    equity_curve = [{"timestamp": _round_timestamp(df["timestamp"].iloc[settings.lookback - 1]), "equity": equity}]
    cost_rate = (settings.fee_percent + settings.slippage_percent) / 100.0
    position_fraction = settings.position_size_percent / 100.0
    next_available_index = settings.lookback
    exposure_candles = 0

    for history_end in range(settings.lookback, end_limit, settings.step):
        history = df.iloc[:history_end]
        forecast_settings = ForecastSettings(
            engine="baseline",
            baseline_model=settings.baseline_model,
            horizon=forecast_horizon,
            lookback=settings.lookback,
            paths=settings.paths,
            block_size=settings.block_size,
            seed=settings.seed + history_end,
            calibration=settings.calibration,
        )
        try:
            result = baseline_forecast(history, forecast_settings)
        except ForecastError as exc:
            raise ValueError(str(exc)) from exc

        last_known_close = float(df["close"].iloc[history_end - 1])
        target_index = history_end + forecast_horizon - 1
        predicted_exit = float(result.forecast["close"].iloc[-1])
        predicted_return = predicted_exit / last_known_close - 1.0
        actual_target_close = float(df["close"].iloc[target_index])
        actual_return = actual_target_close / last_known_close - 1.0
        lower = float(result.forecast["lower_close"].iloc[-1])
        upper = float(result.forecast["upper_close"].iloc[-1])
        forecast_records.append(
            {
                "error_percent": (predicted_exit / actual_target_close - 1.0) * 100.0,
                "direction_correct": float(np.sign(predicted_return) == np.sign(actual_return)),
                "covered": float(lower <= actual_target_close <= upper),
                "interval_width_percent": (upper / max(lower, np.finfo(float).eps) - 1.0) * 100.0,
            }
        )

        threshold = settings.threshold_percent / 100.0
        if predicted_return > threshold:
            side = 1
        elif predicted_return < -threshold:
            side = -1
        else:
            continue

        if settings.direction == "long_only" and side == -1:
            continue
        if settings.direction == "short_only" and side == 1:
            continue

        entry_index = history_end - 1 + settings.execution_delay
        planned_exit_index = entry_index + settings.horizon - 1
        if planned_exit_index >= len(df):
            continue
        if not settings.allow_overlap and entry_index < next_available_index:
            continue

        entry_price = float(df["open"].iloc[entry_index])
        exit_resolution = _resolve_exit(
            df,
            entry_index,
            planned_exit_index,
            entry_price,
            side,
            settings.stop_loss_percent,
            settings.take_profit_percent,
        )
        net_return = _net_trade_return(entry_price, exit_resolution.price, side, cost_rate)
        portfolio_return = net_return * position_fraction
        portfolio_return = max(portfolio_return, -0.999999)
        equity *= 1.0 + portfolio_return
        equity_values.append(equity)
        exposure_candles += exit_resolution.index - entry_index + 1
        next_available_index = exit_resolution.index + 1

        trade = {
            "signal_timestamp": _round_timestamp(df["timestamp"].iloc[history_end - 1]),
            "entry_timestamp": _round_timestamp(df["timestamp"].iloc[entry_index]),
            "exit_timestamp": _round_timestamp(df["timestamp"].iloc[exit_resolution.index]),
            "side": "long" if side == 1 else "short",
            "entry": round(entry_price, 8),
            "exit": round(exit_resolution.price, 8),
            "exit_reason": exit_resolution.reason,
            "predicted_return_percent": round(predicted_return * 100.0, 3),
            "net_return_percent": round(net_return * 100.0, 3),
            "portfolio_return_percent": round(portfolio_return * 100.0, 3),
            "equity": round(equity, 6),
        }
        trades.append(trade)
        equity_curve.append({"timestamp": trade["exit_timestamp"], "equity": round(equity, 8)})
        if equity <= 0:
            break

    forecast_metrics = _forecast_metrics(forecast_records)
    test_start_index = settings.lookback
    test_end_index = len(df) - 1
    benchmark_entry = float(df["open"].iloc[test_start_index])
    benchmark_exit = float(df["close"].iloc[test_end_index])
    benchmark_return = _net_trade_return(benchmark_entry, benchmark_exit, 1, cost_rate)

    if not trades:
        return {
            "metrics": {
                "trades": 0,
                "total_return_percent": 0.0,
                "benchmark_return_percent": round(benchmark_return * 100.0, 3),
                "excess_return_percent": round(-benchmark_return * 100.0, 3),
                "win_rate_percent": 0.0,
                "max_drawdown_percent": 0.0,
                "profit_factor": 0.0,
                "expectancy_percent": 0.0,
                "exposure_percent": 0.0,
            },
            "forecast_metrics": forecast_metrics,
            "trades": [],
            "equity_curve": equity_curve,
            "notes": [
                "No trades met the selected forecast threshold and direction rules.",
                "Forecast accuracy is still reported because no-trade forecasts are evidence too.",
            ],
        }

    returns = np.asarray([trade["net_return_percent"] / 100.0 for trade in trades], dtype=float)
    wins = returns[returns > 0]
    losses = returns[returns < 0]
    profit_factor = _profit_factor(returns)
    average_win = float(wins.mean()) if len(wins) else 0.0
    average_loss = float(losses.mean()) if len(losses) else 0.0
    payoff_ratio = average_win / abs(average_loss) if average_loss < 0 else math.inf if average_win > 0 else 0.0
    test_candles = max(1, test_end_index - test_start_index + 1)

    metrics = {
        "trades": len(trades),
        "long_trades": sum(trade["side"] == "long" for trade in trades),
        "short_trades": sum(trade["side"] == "short" for trade in trades),
        "total_return_percent": round((equity - 1.0) * 100.0, 3),
        "benchmark_return_percent": round(benchmark_return * 100.0, 3),
        "excess_return_percent": round((equity - 1.0 - benchmark_return) * 100.0, 3),
        "win_rate_percent": round(float((returns > 0).mean() * 100.0), 2),
        "max_drawdown_percent": round(_max_drawdown(equity_values) * 100.0, 3),
        "profit_factor": "∞" if math.isinf(profit_factor) else round(profit_factor, 3),
        "expectancy_percent": round(float(returns.mean() * 100.0), 4),
        "average_win_percent": round(average_win * 100.0, 4),
        "average_loss_percent": round(average_loss * 100.0, 4),
        "payoff_ratio": "∞" if math.isinf(payoff_ratio) else round(payoff_ratio, 3),
        "exposure_percent": round(exposure_candles / test_candles * 100.0, 2),
        "fee_percent_each_side": settings.fee_percent,
        "slippage_percent_each_side": settings.slippage_percent,
        "position_size_percent": settings.position_size_percent,
        "overlapping_positions": settings.allow_overlap,
    }
    metrics.update(_expanded_diagnostics(returns, equity_values))
    exit_counts: dict[str, int] = {}
    for trade in trades:
        exit_counts[trade["exit_reason"]] = exit_counts.get(trade["exit_reason"], 0) + 1

    return {
        "metrics": metrics,
        "forecast_metrics": forecast_metrics,
        "exit_counts": exit_counts,
        "trades": trades[-300:],
        "equity_curve": equity_curve[-1000:],
        "notes": [
            "Each forecast only sees candles available before its signal time.",
            "Trades enter at a later candle open, avoiding the unrealistic assumption that the just-finished close was freely tradable.",
            "Overlapping positions are disabled by default so one unit of capital is not reused several times at once.",
            "Same-bar stop and target collisions are resolved conservatively in favour of the stop.",
            "The backtest uses transparent baselines only. Kronos evaluation needs a verified model training cut-off before it can be called clean out-of-sample.",
            "Past simulated results do not guarantee future performance.",
        ],
    }
