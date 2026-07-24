from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from pydantic import ValidationError

from app.core.config import APP_NAME, APP_VERSION, DATA_DIR, MAX_UPLOAD_BYTES, SETTINGS
from app.core.errors import MarketForgeError
from app.core.schemas import BacktestSettings, ComparisonSettings, ForecastSettings
from app.services.backtest_service import run_walk_forward_backtest
from app.services.comparison_service import compare_baselines
from app.services.data_service import dataframe_profile, load_csv_bytes, normalise_market_data, rows_for_json
from app.services.forecast_service import create_forecast, kronos_status

router = APIRouter(prefix="/api")
_HEAVY_JOB_SEMAPHORE = asyncio.Semaphore(SETTINGS.max_concurrent_jobs)


async def _run_heavy(func, *args):
    """Bound CPU/GPU-heavy jobs so a few requests cannot exhaust the host."""
    async with _HEAVY_JOB_SEMAPHORE:
        return await run_in_threadpool(func, *args)

_ALLOWED_CONTENT_TYPES = {
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",
    "text/plain",
    "application/octet-stream",
    "",
}


def _parse_settings(payload: str, model_type):
    if len(payload) > 20_000:
        raise HTTPException(status_code=400, detail="The settings payload is too large.")
    try:
        parsed = json.loads(payload or "{}")
        return model_type.model_validate(parsed)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="The settings are not valid JSON.") from exc
    except ValidationError as exc:
        first = exc.errors()[0] if exc.errors() else None
        message = first.get("msg", "The settings are invalid.") if first else "The settings are invalid."
        raise HTTPException(status_code=400, detail=message) from exc


async def _read_upload(file: UploadFile):
    filename = Path(file.filename or "").name
    if not filename or not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file.")
    content_type = (file.content_type or "").split(";", 1)[0].strip().lower()
    if content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="The uploaded file does not look like a CSV.")

    content = await file.read(MAX_UPLOAD_BYTES + 1)
    await file.close()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"The file is larger than {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
        )
    try:
        raw = await run_in_threadpool(load_csv_bytes, content)
        return await run_in_threadpool(normalise_market_data, raw)
    except MarketForgeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/health")
def health() -> dict:
    status = kronos_status()
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "status": "ready",
        "environment": SETTINGS.environment,
        "kronos": status,
        "max_concurrent_jobs": SETTINGS.max_concurrent_jobs,
    }


@router.get("/engines")
def engines() -> dict:
    return {
        "baseline": {
            "available": True,
            "models": ["ensemble", "block_bootstrap", "drift", "naive"],
            "recommended": "ensemble",
        },
        "kronos": kronos_status(),
    }


@router.get("/research-integrity")
def research_integrity() -> dict:
    return {
        "principles": [
            "Chronological evaluation only.",
            "Signals are created before simulated entry prices are known.",
            "Overlapping capital is disabled by default.",
            "No model result is labelled clean out-of-sample without a verified training cut-off.",
            "No-trade forecasts remain part of accuracy statistics.",
        ],
        "kronos_oos_status": "unverified-training-cutoff",
    }


@router.get("/sample")
def sample_file() -> FileResponse:
    return FileResponse(DATA_DIR / "sample_market_data.csv", filename="sample_market_data.csv")


@router.post("/analyse")
async def analyse(file: UploadFile = File(...)) -> dict:
    df, report = await _read_upload(file)
    return {
        "report": report.as_dict(),
        "profile": dataframe_profile(df),
        "preview": rows_for_json(df.tail(100)),
        "columns": list(df.columns),
    }


@router.post("/forecast")
async def forecast(
    file: UploadFile = File(...),
    settings_json: str = Form("{}"),
) -> dict:
    settings = _parse_settings(settings_json, ForecastSettings)
    df, report = await _read_upload(file)
    try:
        result = await _run_heavy(create_forecast, df, settings)
    except MarketForgeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    output = result.as_dict()
    output["data_report"] = report.as_dict()
    output["data_profile"] = dataframe_profile(df)
    return output


@router.post("/backtest")
async def backtest(
    file: UploadFile = File(...),
    settings_json: str = Form("{}"),
) -> dict:
    settings = _parse_settings(settings_json, BacktestSettings)
    df, report = await _read_upload(file)
    try:
        result = await _run_heavy(run_walk_forward_backtest, df, settings)
    except (ValueError, MarketForgeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    result["data_report"] = report.as_dict()
    result["data_profile"] = dataframe_profile(df)
    return result


@router.post("/compare")
async def compare(
    file: UploadFile = File(...),
    settings_json: str = Form("{}"),
) -> dict:
    settings = _parse_settings(settings_json, ComparisonSettings)
    df, report = await _read_upload(file)
    try:
        result = await _run_heavy(compare_baselines, df, settings)
    except (ValueError, MarketForgeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    result["data_report"] = report.as_dict()
    result["data_profile"] = dataframe_profile(df)
    return result
