from __future__ import annotations

import numpy as np
import pytest

from app.core.schemas import ForecastSettings
from app.services.forecast_service import baseline_forecast, create_forecast


@pytest.mark.parametrize("model", ["ensemble", "block_bootstrap", "drift", "naive"])
def test_baseline_models_return_valid_candles(market_df, model: str) -> None:
    settings = ForecastSettings(
        engine="baseline",
        baseline_model=model,
        horizon=20,
        lookback=180,
        paths=60,
        block_size=6,
        seed=123,
    )
    result = baseline_forecast(market_df, settings)
    output = result.forecast

    assert len(output) == 20
    assert np.isfinite(output.select_dtypes(include="number").to_numpy()).all()
    assert (output["high"] >= output[["open", "close"]].max(axis=1)).all()
    assert (output["low"] <= output[["open", "close"]].min(axis=1)).all()
    assert (output["low"] > 0).all()
    assert (output["volume"] >= 0).all()
    assert (output["lower_close"] <= output["close"]).all()
    assert (output["close"] <= output["upper_close"]).all()


def test_baseline_is_reproducible_for_same_seed(market_df) -> None:
    settings = ForecastSettings(
        engine="baseline", horizon=12, lookback=120, paths=40, block_size=4, seed=7
    )
    first = baseline_forecast(market_df, settings)
    second = baseline_forecast(market_df, settings)

    assert first.forecast.equals(second.forecast)
    assert first.metadata["reproducible"] is True


def test_different_seed_changes_stochastic_forecast(market_df) -> None:
    first = baseline_forecast(
        market_df, ForecastSettings(engine="baseline", horizon=12, paths=40, seed=1)
    )
    second = baseline_forecast(
        market_df, ForecastSettings(engine="baseline", horizon=12, paths=40, seed=2)
    )

    assert not first.forecast["close"].equals(second.forecast["close"])


def test_explicit_baseline_does_not_try_kronos(market_df) -> None:
    result = create_forecast(
        market_df,
        ForecastSettings(engine="baseline", baseline_model="naive", horizon=5, paths=20),
    )
    assert result.engine == "baseline-naive"
    assert result.fallback is None
