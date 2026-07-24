from __future__ import annotations

import io

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def market_df() -> pd.DataFrame:
    rows = 360
    rng = np.random.default_rng(20260723)
    changes = rng.normal(0.00035, 0.008, rows)
    close = 100.0 * np.exp(np.cumsum(changes))
    previous = np.r_[close[0], close[:-1]]
    gap = rng.normal(0, 0.0015, rows)
    open_ = previous * np.exp(gap)
    high = np.maximum(open_, close) * (1 + rng.uniform(0.001, 0.012, rows))
    low = np.minimum(open_, close) * (1 - rng.uniform(0.001, 0.012, rows))
    volume = rng.lognormal(mean=8.0, sigma=0.45, size=rows)
    timestamp = pd.date_range("2025-01-01", periods=rows, freq="h", tz="UTC")
    amount = volume * (open_ + high + low + close) / 4
    return pd.DataFrame(
        {
            "timestamp": timestamp,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
            "amount": amount,
        }
    )


@pytest.fixture
def market_csv(market_df: pd.DataFrame) -> bytes:
    buffer = io.StringIO()
    market_df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")
