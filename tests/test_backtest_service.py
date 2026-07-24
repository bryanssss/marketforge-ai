from __future__ import annotations

import pandas as pd

from app.core.schemas import BacktestSettings
from app.services.backtest_service import _resolve_exit, run_walk_forward_backtest


def test_backtest_reports_forecasts_even_when_no_trade(market_df) -> None:
    result = run_walk_forward_backtest(
        market_df,
        BacktestSettings(
            lookback=80,
            horizon=6,
            step=20,
            paths=20,
            threshold_percent=25,
            seed=5,
        ),
    )

    assert result["metrics"]["trades"] == 0
    assert result["forecast_metrics"]["evaluations"] > 0


def test_trade_entry_is_after_signal_and_positions_do_not_overlap_by_default(market_df) -> None:
    result = run_walk_forward_backtest(
        market_df,
        BacktestSettings(
            baseline_model="drift",
            lookback=80,
            horizon=8,
            step=2,
            paths=20,
            threshold_percent=0,
            execution_delay=1,
            allow_overlap=False,
            seed=9,
        ),
    )

    trades = result["trades"]
    assert trades
    for trade in trades:
        assert pd.Timestamp(trade["signal_timestamp"]) < pd.Timestamp(trade["entry_timestamp"])
    for previous, current in zip(trades, trades[1:], strict=False):
        assert pd.Timestamp(previous["exit_timestamp"]) < pd.Timestamp(current["entry_timestamp"])


def test_costs_reduce_backtest_return(market_df) -> None:
    common = dict(
        baseline_model="drift",
        lookback=80,
        horizon=5,
        step=5,
        paths=20,
        threshold_percent=0,
        seed=11,
    )
    free = run_walk_forward_backtest(
        market_df, BacktestSettings(**common, fee_percent=0, slippage_percent=0)
    )
    costly = run_walk_forward_backtest(
        market_df, BacktestSettings(**common, fee_percent=0.5, slippage_percent=0.5)
    )
    assert costly["metrics"]["total_return_percent"] <= free["metrics"]["total_return_percent"]


def test_same_bar_stop_and_target_uses_conservative_stop() -> None:
    df = pd.DataFrame(
        {
            "open": [100.0],
            "high": [110.0],
            "low": [90.0],
            "close": [104.0],
        }
    )
    resolved = _resolve_exit(
        df,
        entry_index=0,
        planned_exit_index=0,
        entry_price=100.0,
        side=1,
        stop_loss_percent=5.0,
        take_profit_percent=5.0,
    )
    assert resolved.reason == "stop_same_bar_conservative"
    assert resolved.price == 95.0
