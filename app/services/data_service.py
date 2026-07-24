from __future__ import annotations

import hashlib
import io
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from app.core.config import MAX_COLUMNS, MAX_ROWS
from app.core.errors import DataValidationError

COLUMN_ALIASES = {
    "time": "timestamp",
    "date": "timestamp",
    "datetime": "timestamp",
    "timestamps": "timestamp",
    "open_time": "timestamp",
    "o": "open",
    "h": "high",
    "l": "low",
    "c": "close",
    "v": "volume",
    "vol": "volume",
    "turnover": "amount",
    "quote_volume": "amount",
}
REQUIRED = ("open", "high", "low", "close")


@dataclass(frozen=True)
class DataReport:
    rows_received: int
    rows_kept: int
    duplicates_removed: int
    invalid_rows_removed: int
    candles_repaired: int
    volume_values_repaired: int
    amount_values_repaired: int
    amount_values_inferred: int
    inferred_interval: str
    interval_seconds: float
    irregular_intervals: int
    estimated_missing_candles: int
    largest_gap: str
    outlier_returns: int
    start_timestamp: str
    end_timestamp: str
    timezone: str
    has_volume: bool
    has_amount: bool
    quality_score: int
    data_fingerprint: str
    warnings: list[str]

    def as_dict(self) -> dict:
        return asdict(self)


def load_csv_bytes(content: bytes) -> pd.DataFrame:
    if not content:
        raise DataValidationError("The uploaded CSV is empty.")
    if b"\x00" in content[:4096]:
        raise DataValidationError("The file contains binary data and does not look like a CSV.")

    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return pd.read_csv(
                io.BytesIO(content),
                encoding=encoding,
                low_memory=False,
                on_bad_lines="error",
            )
        except UnicodeDecodeError as exc:
            last_error = exc
            continue
        except pd.errors.EmptyDataError as exc:
            raise DataValidationError("The CSV does not contain a header and data rows.") from exc
        except pd.errors.ParserError as exc:
            raise DataValidationError("The CSV structure is invalid or contains broken rows.") from exc
        except Exception as exc:  # pandas can wrap parser errors differently between versions
            last_error = exc
            break
    raise DataValidationError("The file could not be read as a normal CSV.") from last_error


def _normalise_columns(columns: list[object]) -> list[str]:
    output: list[str] = []
    for column in columns:
        name = str(column).strip().lower().replace(" ", "_").replace("-", "_")
        output.append(COLUMN_ALIASES.get(name, name))
    if len(set(output)) != len(output):
        duplicates = sorted({name for name in output if output.count(name) > 1})
        raise DataValidationError(
            "Two or more columns resolve to the same name: " + ", ".join(duplicates)
        )
    return output


def _infer_interval(timestamps: pd.Series) -> tuple[pd.Timedelta, pd.Series]:
    diffs = timestamps.diff().dropna()
    positive = diffs[diffs > pd.Timedelta(0)]
    if positive.empty:
        return pd.Timedelta(hours=1), positive

    rounded_seconds = positive.dt.total_seconds().round().astype("int64")
    mode = rounded_seconds.mode()
    seconds = int(mode.iloc[0]) if not mode.empty else int(round(positive.median().total_seconds()))
    if seconds <= 0:
        seconds = 3600
    return pd.Timedelta(seconds=seconds), positive


def _fingerprint(df: pd.DataFrame) -> str:
    canonical = df.copy()
    canonical["timestamp"] = canonical["timestamp"].astype("int64")
    numeric_columns = [name for name in canonical.columns if name != "timestamp"]
    canonical[numeric_columns] = canonical[numeric_columns].round(10)
    hashed = pd.util.hash_pandas_object(canonical, index=False).to_numpy(dtype="uint64")
    return hashlib.sha256(hashed.tobytes()).hexdigest()[:16]


def _quality_score(
    rows_received: int,
    invalid: int,
    duplicates: int,
    repaired: int,
    irregular: int,
    outliers: int,
    warnings: int,
) -> int:
    denominator = max(rows_received, 1)
    penalty = 0.0
    penalty += min(35.0, invalid / denominator * 160)
    penalty += min(15.0, duplicates / denominator * 100)
    penalty += min(20.0, repaired / denominator * 80)
    penalty += min(15.0, irregular / max(denominator - 1, 1) * 80)
    penalty += min(10.0, outliers / denominator * 80)
    penalty += min(10.0, warnings * 2.0)
    return max(0, min(100, int(round(100 - penalty))))


def normalise_market_data(raw: pd.DataFrame) -> tuple[pd.DataFrame, DataReport]:
    if raw.empty:
        raise DataValidationError("The CSV has no rows.")
    if len(raw) > MAX_ROWS:
        raise DataValidationError(f"The CSV contains too many rows. Maximum: {MAX_ROWS:,}.")
    if len(raw.columns) > MAX_COLUMNS:
        raise DataValidationError(f"The CSV contains too many columns. Maximum: {MAX_COLUMNS}.")

    df = raw.copy()
    df.columns = _normalise_columns(list(df.columns))

    missing = [name for name in REQUIRED if name not in df.columns]
    if missing:
        raise DataValidationError("Missing required column(s): " + ", ".join(missing))

    warnings: list[str] = []
    rows_received = len(df)
    has_volume = "volume" in df.columns
    has_amount = "amount" in df.columns

    if "timestamp" not in df.columns:
        df["timestamp"] = pd.date_range("2024-01-01", periods=len(df), freq="h", tz="UTC")
        warnings.append("No timestamp column was found, so artificial hourly UTC timestamps were created.")
    else:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)

    if not has_volume:
        df["volume"] = 0.0
        warnings.append("No volume column was found; volume was set to zero.")
    if not has_amount:
        warnings.append(
            "No amount/turnover column was found; it was estimated from volume and the typical candle price."
        )

    numeric = [*REQUIRED, "volume"]
    if has_amount:
        numeric.append("amount")
    for name in numeric:
        df[name] = pd.to_numeric(df[name], errors="coerce")
        df[name] = df[name].replace([np.inf, -np.inf], np.nan)

    before_invalid = len(df)
    df = df.dropna(subset=["timestamp", *REQUIRED])
    df = df[(df[list(REQUIRED)] > 0).all(axis=1)]
    invalid_rows_removed = before_invalid - len(df)

    before_duplicates = len(df)
    df = df.sort_values("timestamp", kind="stable").drop_duplicates(subset="timestamp", keep="last")
    duplicates_removed = before_duplicates - len(df)

    if len(df) < 40:
        raise DataValidationError("At least 40 valid candles are required after cleaning.")

    expected_high = df[["open", "close", "high"]].max(axis=1)
    expected_low = df[["open", "close", "low"]].min(axis=1)
    repaired_mask = (df["high"] < df[["open", "close"]].max(axis=1)) | (
        df["low"] > df[["open", "close"]].min(axis=1)
    )
    candles_repaired = int(repaired_mask.sum())
    df["high"] = expected_high
    df["low"] = expected_low

    volume_bad = df["volume"].isna() | (df["volume"] < 0)
    volume_values_repaired = int(volume_bad.sum())
    df["volume"] = df["volume"].fillna(0).clip(lower=0)

    amount_values_repaired = 0
    amount_values_inferred = 0
    if has_amount:
        amount_bad = df["amount"].isna() | (df["amount"] < 0)
        amount_values_repaired = int(amount_bad.sum())
        df["amount"] = df["amount"].fillna(0).clip(lower=0)
    else:
        typical_price = df[["open", "high", "low", "close"]].mean(axis=1)
        df["amount"] = (df["volume"] * typical_price).clip(lower=0)
        amount_values_inferred = len(df)

    interval, positive_diffs = _infer_interval(df["timestamp"])
    tolerance_seconds = max(1.0, interval.total_seconds() * 0.01)
    if positive_diffs.empty:
        irregular_mask = pd.Series([], dtype=bool)
    else:
        irregular_mask = (positive_diffs - interval).abs().dt.total_seconds() > tolerance_seconds
    irregular_intervals = int(irregular_mask.sum())

    estimated_missing_candles = 0
    if not positive_diffs.empty and interval.total_seconds() > 0:
        ratios = positive_diffs.dt.total_seconds() / interval.total_seconds()
        estimated_missing_candles = int(np.maximum(np.rint(ratios).astype(int) - 1, 0).sum())
    largest_gap_delta = positive_diffs.max() if not positive_diffs.empty else interval
    largest_gap = str(largest_gap_delta)

    log_returns = np.log(df["close"]).diff().dropna()
    outlier_returns = 0
    if len(log_returns) >= 20:
        median = float(log_returns.median())
        mad = float(np.median(np.abs(log_returns - median)))
        if mad > 0:
            robust_z = np.abs(log_returns - median) / (1.4826 * mad)
            outlier_returns = int((robust_z > 12).sum())

    if invalid_rows_removed:
        warnings.append(f"{invalid_rows_removed} row(s) with invalid timestamps or prices were removed.")
    if duplicates_removed:
        warnings.append(f"{duplicates_removed} duplicate timestamp row(s) were removed.")
    if candles_repaired:
        warnings.append(f"{candles_repaired} candle(s) had impossible high/low relationships and were repaired.")
    if irregular_intervals:
        warnings.append(
            "The timestamps contain gaps or irregular spacing. Market closures may be normal, but forecasts use the most common interval."
        )
    if outlier_returns:
        warnings.append(
            f"{outlier_returns} unusually large price move(s) were detected. Check for splits, bad ticks or regime changes."
        )

    keep = ["timestamp", "open", "high", "low", "close", "volume", "amount"]
    df = df[keep].reset_index(drop=True)

    fingerprint = _fingerprint(df)
    quality_score = _quality_score(
        rows_received,
        invalid_rows_removed,
        duplicates_removed,
        candles_repaired + volume_values_repaired + amount_values_repaired,
        irregular_intervals,
        outlier_returns,
        len(warnings),
    )

    report = DataReport(
        rows_received=rows_received,
        rows_kept=len(df),
        duplicates_removed=duplicates_removed,
        invalid_rows_removed=invalid_rows_removed,
        candles_repaired=candles_repaired,
        volume_values_repaired=volume_values_repaired,
        amount_values_repaired=amount_values_repaired,
        amount_values_inferred=amount_values_inferred,
        inferred_interval=str(interval),
        interval_seconds=float(interval.total_seconds()),
        irregular_intervals=irregular_intervals,
        estimated_missing_candles=estimated_missing_candles,
        largest_gap=largest_gap,
        outlier_returns=outlier_returns,
        start_timestamp=_format_timestamp(df["timestamp"].iloc[0]),
        end_timestamp=_format_timestamp(df["timestamp"].iloc[-1]),
        timezone="UTC",
        has_volume=has_volume,
        has_amount=has_amount,
        quality_score=quality_score,
        data_fingerprint=fingerprint,
        warnings=warnings,
    )
    return df, report


def infer_step(df: pd.DataFrame) -> pd.Timedelta:
    step, _ = _infer_interval(df["timestamp"])
    return step


def _format_timestamp(value: object) -> str:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    return timestamp.isoformat().replace("+00:00", "Z")


def rows_for_json(df: pd.DataFrame) -> list[dict]:
    output = df.copy()
    output["timestamp"] = output["timestamp"].map(_format_timestamp)
    output = output.replace([np.inf, -np.inf], np.nan).where(pd.notnull(output), None)
    return output.to_dict(orient="records")


def dataframe_profile(df: pd.DataFrame) -> dict:
    close = df["close"].astype(float)
    returns = np.log(close).diff().dropna()
    return {
        "rows": len(df),
        "start": _format_timestamp(df["timestamp"].iloc[0]),
        "end": _format_timestamp(df["timestamp"].iloc[-1]),
        "last_close": round(float(close.iloc[-1]), 8),
        "median_volume": round(float(df["volume"].median()), 4),
        "return_volatility_percent": round(float(returns.std(ddof=1) * 100), 4) if len(returns) > 1 else 0.0,
    }
