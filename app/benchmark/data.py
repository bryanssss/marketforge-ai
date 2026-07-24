from __future__ import annotations

import csv
import hashlib
import io
import time
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from app.benchmark.spec import FrozenSpec, write_json

_BINANCE_COLUMNS = [
    "open_time", "open", "high", "low", "close", "volume", "close_time",
    "quote_asset_volume", "trades", "taker_buy_base", "taker_buy_quote", "ignore",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def month_keys(start_iso: str, end_iso_exclusive: str) -> list[str]:
    start = pd.Timestamp(start_iso).tz_convert("UTC")
    end = pd.Timestamp(end_iso_exclusive).tz_convert("UTC")
    months = pd.period_range(start=start.tz_localize(None).to_period("M"), end=(end - pd.Timedelta(seconds=1)).tz_localize(None).to_period("M"), freq="M")
    return [period.strftime("%Y-%m") for period in months]


def archive_url(symbol: str, interval: str, month: str) -> str:
    filename = f"{symbol}-{interval}-{month}.zip"
    return f"https://data.binance.vision/data/spot/monthly/klines/{symbol}/{interval}/{filename}"


def parse_checksum(text: str) -> str:
    token = text.strip().split()[0].lower() if text.strip() else ""
    if len(token) != 64 or any(char not in "0123456789abcdef" for char in token):
        raise ValueError("The provider checksum is not a valid SHA-256 value.")
    return token


def download(
    url: str,
    destination: Path,
    timeout: int = 90,
    retries: int = 3,
) -> None:
    if not url.startswith("https://data.binance.vision/"):
        raise ValueError("The frozen downloader only permits the official Binance HTTPS host.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(
        url, headers={"User-Agent": "MarketForge-Benchmark/0.4"}
    )
    last_error: Exception | None = None
    for attempt in range(max(1, retries)):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response, partial.open("wb") as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
            partial.replace(destination)
            return
        except (OSError, urllib.error.URLError) as exc:
            last_error = exc
            partial.unlink(missing_ok=True)
            if attempt + 1 < retries:
                time.sleep(min(2**attempt, 4))
    raise RuntimeError(f"Could not download {url} after {retries} attempt(s).") from last_error


def _timestamp_unit(value: int) -> str:
    return "us" if abs(value) >= 1_000_000_000_000_000 else "ms"


def parse_binance_zip(path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError(f"ZIP integrity check failed for {path.name}.")
        members = [info for info in archive.infolist() if not info.is_dir()]
        if len(members) != 1 or not members[0].filename.lower().endswith(".csv"):
            raise ValueError(f"Expected exactly one CSV in {path.name}.")
        if members[0].file_size > 50 * 1024 * 1024:
            raise ValueError(f"Uncompressed CSV is unexpectedly large in {path.name}.")
        raw = archive.read(members[0])
    frame = pd.read_csv(io.BytesIO(raw), header=None, names=_BINANCE_COLUMNS)
    if frame.empty:
        raise ValueError(f"{path.name} contains no rows.")
    first = int(frame["open_time"].iloc[0])
    frame["timestamp"] = pd.to_datetime(frame["open_time"], unit=_timestamp_unit(first), utc=True)
    output = frame[["timestamp", "open", "high", "low", "close", "volume", "quote_asset_volume"]].copy()
    output = output.rename(columns={"quote_asset_volume": "amount"})
    for column in ("open", "high", "low", "close", "volume", "amount"):
        output[column] = pd.to_numeric(output[column], errors="raise")
    return output


def validate_canonical_frame(
    frame: pd.DataFrame,
    spec: FrozenSpec,
    symbol: str,
) -> dict[str, Any]:
    expected_columns = ["timestamp", "open", "high", "low", "close", "volume", "amount"]
    if list(frame.columns) != expected_columns:
        raise ValueError(f"{symbol} canonical columns do not match the frozen schema.")
    if frame.empty:
        raise ValueError(f"{symbol} canonical dataset is empty.")
    timestamps = pd.to_datetime(frame["timestamp"], utc=True, errors="raise")
    if not timestamps.is_monotonic_increasing or timestamps.duplicated().any():
        raise ValueError(f"{symbol} timestamps must be strictly increasing and unique.")
    start = pd.Timestamp(spec.raw["data"]["context_start"])
    end = pd.Timestamp(spec.raw["data"]["holdout_end_exclusive"])
    interval = spec.raw["data"]["interval"]
    expected_index = pd.date_range(start=start, end=end, inclusive="left", freq=interval)
    actual_index = pd.DatetimeIndex(timestamps)
    missing = expected_index.difference(actual_index)
    unexpected = actual_index.difference(expected_index)
    if len(missing) or len(unexpected) or len(actual_index) != len(expected_index):
        raise ValueError(
            f"{symbol} does not provide the exact frozen hourly coverage: "
            f"missing={len(missing)}, unexpected={len(unexpected)}."
        )
    numeric = frame[expected_columns[1:]].to_numpy(dtype=float)
    if not np.isfinite(numeric).all():
        raise ValueError(f"{symbol} contains non-finite numeric values.")
    if (frame[["open", "high", "low", "close"]] <= 0).any().any():
        raise ValueError(f"{symbol} contains non-positive prices.")
    if (frame[["volume", "amount"]] < 0).any().any():
        raise ValueError(f"{symbol} contains negative volume or amount.")
    if (frame["high"] < frame[["open", "close"]].max(axis=1)).any():
        raise ValueError(f"{symbol} contains an invalid high price.")
    if (frame["low"] > frame[["open", "close"]].min(axis=1)).any():
        raise ValueError(f"{symbol} contains an invalid low price.")
    return {
        "expected_rows": int(len(expected_index)),
        "missing_timestamps": 0,
        "unexpected_timestamps": 0,
        "schema": expected_columns,
    }


def freeze_data(
    spec: FrozenSpec,
    root: Path,
    *,
    force: bool = False,
    now: datetime | None = None,
) -> dict[str, Any]:
    ready_value = spec.raw["data"].get("data_available_not_before")
    if ready_value:
        ready_at = datetime.fromisoformat(str(ready_value).replace("Z", "+00:00"))
        current = now or datetime.now(timezone.utc)
        if current < ready_at:
            raise ValueError(
                "Prospective holdout data is not complete yet. The frozen protocol may collect data "
                f"on or after {ready_at.isoformat()}."
            )
    data_dir = root / "data"
    archives_dir = data_dir / "archives"
    canonical_dir = data_dir / "canonical"
    archives_dir.mkdir(parents=True, exist_ok=True)
    canonical_dir.mkdir(parents=True, exist_ok=True)
    interval = spec.raw["data"]["interval"]
    months = month_keys(spec.raw["data"]["context_start"], spec.raw["data"]["holdout_end_exclusive"])
    datasets: list[dict[str, Any]] = []
    archives: list[dict[str, Any]] = []

    for symbol in spec.assets:
        parts: list[pd.DataFrame] = []
        for month in months:
            url = archive_url(symbol, interval, month)
            zip_path = archives_dir / Path(url).name
            checksum_path = archives_dir / f"{zip_path.name}.CHECKSUM"
            if force or not zip_path.exists():
                download(url, zip_path)
            if force or not checksum_path.exists():
                download(url + ".CHECKSUM", checksum_path)
            expected = parse_checksum(checksum_path.read_text(encoding="utf-8"))
            actual = sha256_file(zip_path)
            if actual != expected:
                raise ValueError(f"Checksum mismatch for {zip_path.name}: expected {expected}, found {actual}.")
            parts.append(parse_binance_zip(zip_path))
            archives.append(
                {
                    "symbol": symbol,
                    "interval": interval,
                    "month": month,
                    "url": url,
                    "checksum_url": url + ".CHECKSUM",
                    "archive_path": str(zip_path.relative_to(root)),
                    "checksum_path": str(checksum_path.relative_to(root)),
                    "provider_sha256": expected,
                    "downloaded_sha256": actual,
                    "checksum_file_sha256": sha256_file(checksum_path),
                    "bytes": zip_path.stat().st_size,
                }
            )

        frame = pd.concat(parts, ignore_index=True).sort_values("timestamp", kind="stable")
        if frame["timestamp"].duplicated().any():
            raise ValueError(
                f"Duplicate provider timestamps detected for {symbol}; frozen data are rejected, not repaired."
            )
        start = pd.Timestamp(spec.raw["data"]["context_start"])
        end = pd.Timestamp(spec.raw["data"]["holdout_end_exclusive"])
        frame = frame[(frame["timestamp"] >= start) & (frame["timestamp"] < end)].reset_index(drop=True)
        quality = validate_canonical_frame(frame, spec, symbol)
        canonical_path = canonical_dir / f"{symbol}-{interval}.csv"
        frame.to_csv(
            canonical_path,
            index=False,
            date_format="%Y-%m-%dT%H:%M:%S.%fZ",
            float_format="%.17g",
            quoting=csv.QUOTE_MINIMAL,
        )
        datasets.append({
            "symbol": symbol,
            "interval": interval,
            "path": str(canonical_path.relative_to(root)),
            "sha256": sha256_file(canonical_path),
            "rows": len(frame),
            "start": frame["timestamp"].iloc[0].isoformat(),
            "end": frame["timestamp"].iloc[-1].isoformat(),
            **quality,
        })

    lock = {
        "benchmark_id": spec.benchmark_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "provider": "binance-public-data",
        "provider_checksum_verified": True,
        "canonical_schema_version": "1.0.0",
        "status": "verified",
        "archives": archives,
        "datasets": datasets,
    }
    write_json(root / "data_lock.json", lock)
    return lock


def verify_data_lock(root: Path, lock: dict[str, Any], spec: FrozenSpec | None = None) -> list[str]:
    problems: list[str] = []
    if lock.get("status") != "verified": problems.append("Data lock status is not verified.")
    if lock.get("provider_checksum_verified") is not True: problems.append("Provider archive checksums are not marked verified.")
    if spec is not None and lock.get("benchmark_id") != spec.benchmark_id: problems.append("Data lock benchmark identifier does not match the specification.")
    seen_archives: set[tuple[str, str]] = set()
    for item in lock.get("archives", []):
        key = (str(item.get("symbol")), str(item.get("month")))
        if key in seen_archives: problems.append(f"Duplicate archive lock entry: {key[0]} {key[1]}")
        seen_archives.add(key)
        archive = root / str(item.get("archive_path", "")); checksum = root / str(item.get("checksum_path", ""))
        if not archive.is_file(): problems.append(f"Missing provider archive: {archive}")
        elif sha256_file(archive) != item.get("provider_sha256") or item.get("downloaded_sha256") != item.get("provider_sha256"): problems.append(f"Provider archive hash mismatch: {archive}")
        if not checksum.is_file(): problems.append(f"Missing provider checksum file: {checksum}")
        else:
            if sha256_file(checksum) != item.get("checksum_file_sha256"): problems.append(f"Checksum-file hash mismatch: {checksum}")
            try:
                if parse_checksum(checksum.read_text(encoding="utf-8")) != item.get("provider_sha256"): problems.append(f"Checksum contents changed: {checksum}")
            except (OSError, ValueError) as exc: problems.append(f"Invalid checksum file {checksum}: {exc}")
    for item in lock.get("datasets", []):
        path = root / item["path"]
        if not path.exists(): problems.append(f"Missing canonical dataset: {path}"); continue
        if sha256_file(path) != item.get("sha256"): problems.append(f"Canonical dataset hash mismatch: {path}"); continue
        if spec is not None:
            try:
                frame = pd.read_csv(path, parse_dates=["timestamp"]); validate_canonical_frame(frame, spec, str(item.get("symbol", path.stem)))
            except (OSError, ValueError, pd.errors.ParserError) as exc: problems.append(f"Canonical dataset validation failed for {path}: {exc}")
    if spec is not None:
        if len(lock.get("datasets", [])) != len(spec.assets): problems.append("Data lock does not contain exactly one dataset per frozen symbol.")
        expected_archives = len(spec.assets) * len(month_keys(spec.raw["data"]["context_start"], spec.raw["data"]["holdout_end_exclusive"]))
        if len(lock.get("archives", [])) != expected_archives: problems.append(f"Data lock contains {len(lock.get('archives', []))} archives; expected {expected_archives}.")
    return problems
