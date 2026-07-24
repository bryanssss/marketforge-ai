from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATIC_DIR = PROJECT_ROOT / "app" / "static"
DATA_DIR = PROJECT_ROOT / "data"
VENDOR_DIR = PROJECT_ROOT / "vendor"
KRONOS_DIR = VENDOR_DIR / "Kronos"


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_csv(name: str, default: str) -> tuple[str, ...]:
    value = os.getenv(name, default)
    items = tuple(item.strip() for item in value.split(",") if item.strip())
    return items or ("localhost",)


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    app_name: str = "MarketForge AI"
    app_version: str = "0.5.0"
    environment: str = os.getenv("MARKETFORGE_ENV", "local")
    host: str = os.getenv("MARKETFORGE_HOST", "127.0.0.1")
    port: int = _env_int("MARKETFORGE_PORT", 7070)
    docs_enabled: bool = _env_bool("MARKETFORGE_DOCS", True)
    allowed_hosts: tuple[str, ...] = _env_csv(
        "MARKETFORGE_ALLOWED_HOSTS", "127.0.0.1,localhost,testserver"
    )
    max_upload_bytes: int = _env_int("MARKETFORGE_MAX_UPLOAD_BYTES", 15 * 1024 * 1024)
    max_request_bytes: int = _env_int("MARKETFORGE_MAX_REQUEST_BYTES", 17 * 1024 * 1024)
    max_rows: int = _env_int("MARKETFORGE_MAX_ROWS", 250_000)
    max_columns: int = _env_int("MARKETFORGE_MAX_COLUMNS", 64)
    max_backtest_evaluations: int = _env_int("MARKETFORGE_MAX_BACKTEST_EVALUATIONS", 750)
    max_comparison_evaluations: int = _env_int("MARKETFORGE_MAX_COMPARISON_EVALUATIONS", 2_000)
    max_benchmark_origins: int = _env_int("MARKETFORGE_MAX_BENCHMARK_ORIGINS", 10_000)
    max_concurrent_jobs: int = max(1, _env_int("MARKETFORGE_MAX_CONCURRENT_JOBS", 2))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


SETTINGS = get_settings()
APP_NAME = SETTINGS.app_name
APP_VERSION = SETTINGS.app_version
MAX_UPLOAD_BYTES = SETTINGS.max_upload_bytes
MAX_ROWS = SETTINGS.max_rows
MAX_COLUMNS = SETTINGS.max_columns
