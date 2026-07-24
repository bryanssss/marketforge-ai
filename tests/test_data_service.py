from __future__ import annotations

import pandas as pd
import pytest

from app.core.errors import DataValidationError
from app.services.data_service import load_csv_bytes, normalise_market_data, rows_for_json


def test_repairs_invalid_candle_negative_volume_and_infers_amount() -> None:
    raw = pd.DataFrame(
        {
            "date": pd.date_range("2025-01-01", periods=45, freq="h"),
            "open": [100.0] * 45,
            "high": [99.0] + [102.0] * 44,
            "low": [101.0] + [98.0] * 44,
            "close": [100.5] * 45,
            "volume": [-1.0] + [10.0] * 44,
        }
    )

    clean, report = normalise_market_data(raw)

    assert (clean["high"] >= clean[["open", "close"]].max(axis=1)).all()
    assert (clean["low"] <= clean[["open", "close"]].min(axis=1)).all()
    assert (clean["volume"] >= 0).all()
    assert (clean["amount"] >= 0).all()
    assert report.candles_repaired == 1
    assert report.volume_values_repaired == 1
    assert report.amount_values_inferred == 45
    assert report.has_amount is False


def test_sorts_and_deduplicates_timestamps(market_df: pd.DataFrame) -> None:
    duplicate = market_df.iloc[[12]].copy()
    duplicate["close"] = duplicate["close"] * 1.01
    raw = pd.concat([market_df.iloc[::-1], duplicate], ignore_index=True)

    clean, report = normalise_market_data(raw)

    assert clean["timestamp"].is_monotonic_increasing
    assert clean["timestamp"].is_unique
    assert report.duplicates_removed == 1
    assert report.timezone == "UTC"


def test_rejects_alias_collision(market_df: pd.DataFrame) -> None:
    raw = market_df.copy()
    raw["date"] = raw["timestamp"]
    with pytest.raises(DataValidationError, match="same name"):
        normalise_market_data(raw)


def test_rejects_missing_required_columns() -> None:
    raw = pd.DataFrame({"timestamp": pd.date_range("2025-01-01", periods=45), "close": 10})
    with pytest.raises(DataValidationError, match="Missing required"):
        normalise_market_data(raw)


def test_rejects_binary_and_empty_csv() -> None:
    with pytest.raises(DataValidationError, match="empty"):
        load_csv_bytes(b"")
    with pytest.raises(DataValidationError, match="binary"):
        load_csv_bytes(b"open,high\x00low,close")


def test_rows_for_json_uses_utc_z(market_df: pd.DataFrame) -> None:
    output = rows_for_json(market_df.head(1))
    assert output[0]["timestamp"].endswith("Z")
