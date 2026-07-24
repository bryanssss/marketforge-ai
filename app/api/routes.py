from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi import APIRouter, Body, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, Response
from pydantic import ValidationError

from app.core.config import APP_NAME, APP_VERSION, DATA_DIR, MAX_UPLOAD_BYTES, SETTINGS
from app.core.errors import MarketForgeError
from app.core.schemas import (
    BacktestSettings,
    ComparisonSettings,
    ConnectorRequest,
    ExperimentPayload,
    ForecastSettings,
    ModelRecordPayload,
    PortfolioSettings,
    ProjectPayload,
    ReplicationRequest,
    ReportRequest,
    StressSettings,
    VolatilitySettings,
)
from app.services.backtest_service import run_walk_forward_backtest
from app.services.comparison_service import compare_baselines
from app.services.connectors_service import import_market_data, list_connectors
from app.services.data_service import dataframe_profile, load_csv_bytes, normalise_market_data, rows_for_json
from app.services.forecast_service import create_forecast, kronos_status
from app.services.portfolio_service import analyse_multi_asset, run_portfolio_simulation
from app.services.regime_service import classify_market_regime
from app.services.replication_service import analyse_external_replication
from app.services.report_service import generate_report
from app.services.storage_service import (
    create_experiment,
    create_project,
    delete_project,
    list_experiments,
    list_models,
    list_projects,
    register_model,
)
from app.services.stress_service import run_stress_test
from app.services.volatility_service import forecast_volatility

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
    if len(payload) > 50_000:
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


async def _read_upload_content(file: UploadFile) -> tuple[str, bytes]:
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
    return filename, content


async def _read_upload(file: UploadFile):
    _, content = await _read_upload_content(file)
    try:
        raw = await run_in_threadpool(load_csv_bytes, content)
        return await run_in_threadpool(normalise_market_data, raw)
    except MarketForgeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


async def _read_multiple(files: list[UploadFile], names_json: str = "[]") -> tuple[dict, dict]:
    if not 2 <= len(files) <= 20:
        raise HTTPException(status_code=400, detail="Upload between 2 and 20 asset CSV files.")
    try:
        requested_names = json.loads(names_json or "[]")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Asset names are not valid JSON.") from exc
    datasets = {}
    reports = {}
    for index, file in enumerate(files):
        filename, content = await _read_upload_content(file)
        try:
            raw = await run_in_threadpool(load_csv_bytes, content)
            dataframe, report = await run_in_threadpool(normalise_market_data, raw)
        except MarketForgeError as exc:
            raise HTTPException(status_code=400, detail=f"{filename}: {exc}") from exc
        name = str(requested_names[index]).strip() if index < len(requested_names) else Path(filename).stem
        safe_name = name[:60] or f"asset_{index + 1}"
        if safe_name in datasets:
            safe_name = f"{safe_name}_{index + 1}"
        datasets[safe_name] = dataframe
        reports[safe_name] = report.as_dict()
    return datasets, reports


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
        "capabilities": [
            "forecast",
            "backtest",
            "portfolio",
            "multi_asset",
            "regime",
            "volatility",
            "stress",
            "projects",
            "experiments",
            "model_registry",
            "reports",
            "external_replication",
            "exchange_import",
        ],
    }


@router.get("/engines")
def engines() -> dict:
    return {
        "baseline": {
            "available": True,
            "models": [
                "regime_ensemble",
                "ensemble",
                "block_bootstrap",
                "exponential_smoothing",
                "momentum",
                "mean_reversion",
                "drift",
                "naive",
            ],
            "recommended": "regime_ensemble",
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
            "Portfolio assets are aligned on matching timestamps.",
            "External replication evidence must disclose data and model provenance.",
        ],
        "kronos_oos_status": "unverified-training-cutoff",
    }


@router.get("/sample")
def sample_file() -> FileResponse:
    return FileResponse(DATA_DIR / "sample_market_data.csv", filename="sample_market_data.csv")


@router.get("/connectors")
def connectors() -> dict:
    return {"connectors": list_connectors()}


@router.post("/import-market-data")
async def import_data(request: ConnectorRequest = Body(...)) -> dict:
    try:
        dataframe, report, metadata = await _run_heavy(import_market_data, request)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "metadata": metadata,
        "report": report.as_dict(),
        "profile": dataframe_profile(dataframe),
        "preview": rows_for_json(dataframe.tail(200)),
        "csv": dataframe.to_csv(index=False),
    }


@router.post("/analyse")
async def analyse(file: UploadFile = File(...)) -> dict:
    df, report = await _read_upload(file)
    return {
        "report": report.as_dict(),
        "profile": dataframe_profile(df),
        "preview": rows_for_json(df.tail(100)),
        "columns": list(df.columns),
        "regime": classify_market_regime(df),
    }


@router.post("/forecast")
async def forecast(file: UploadFile = File(...), settings_json: str = Form("{}")) -> dict:
    settings = _parse_settings(settings_json, ForecastSettings)
    df, report = await _read_upload(file)
    try:
        result = await _run_heavy(create_forecast, df, settings)
    except MarketForgeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    output = result.as_dict()
    output["data_report"] = report.as_dict()
    output["data_profile"] = dataframe_profile(df)
    output["regime"] = classify_market_regime(df, min(settings.lookback, 160))
    return output


@router.post("/backtest")
async def backtest(file: UploadFile = File(...), settings_json: str = Form("{}")) -> dict:
    settings = _parse_settings(settings_json, BacktestSettings)
    df, report = await _read_upload(file)
    try:
        result = await _run_heavy(run_walk_forward_backtest, df, settings)
    except (ValueError, MarketForgeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    result["data_report"] = report.as_dict()
    result["data_profile"] = dataframe_profile(df)
    result["regime"] = classify_market_regime(df, min(settings.lookback, 160))
    return result


@router.post("/compare")
async def compare(file: UploadFile = File(...), settings_json: str = Form("{}")) -> dict:
    settings = _parse_settings(settings_json, ComparisonSettings)
    df, report = await _read_upload(file)
    try:
        result = await _run_heavy(compare_baselines, df, settings)
    except (ValueError, MarketForgeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    result["data_report"] = report.as_dict()
    result["data_profile"] = dataframe_profile(df)
    return result


@router.post("/regime")
async def regime(file: UploadFile = File(...), lookback: int = Form(120)) -> dict:
    df, report = await _read_upload(file)
    try:
        result = classify_market_regime(df, max(20, min(2048, lookback)))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    result["data_report"] = report.as_dict()
    return result


@router.post("/volatility")
async def volatility(file: UploadFile = File(...), settings_json: str = Form("{}")) -> dict:
    settings = _parse_settings(settings_json, VolatilitySettings)
    df, report = await _read_upload(file)
    try:
        result = await _run_heavy(forecast_volatility, df, settings)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    result["data_report"] = report.as_dict()
    return result


@router.post("/stress")
async def stress(file: UploadFile = File(...), settings_json: str = Form("{}")) -> dict:
    settings = _parse_settings(settings_json, StressSettings)
    df, report = await _read_upload(file)
    try:
        result = await _run_heavy(run_stress_test, df, settings)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    result["data_report"] = report.as_dict()
    return result


@router.post("/multi-asset")
async def multi_asset(files: list[UploadFile] = File(...), names_json: str = Form("[]")) -> dict:
    datasets, reports = await _read_multiple(files, names_json)
    try:
        result = await _run_heavy(analyse_multi_asset, datasets)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    result["data_reports"] = reports
    return result


@router.post("/portfolio")
async def portfolio(
    files: list[UploadFile] = File(...), names_json: str = Form("[]"), settings_json: str = Form("{}")
) -> dict:
    settings = _parse_settings(settings_json, PortfolioSettings)
    datasets, reports = await _read_multiple(files, names_json)
    try:
        result = await _run_heavy(run_portfolio_simulation, datasets, settings)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    result["data_reports"] = reports
    return result


@router.get("/projects")
def projects() -> dict:
    return {"projects": list_projects()}


@router.post("/projects")
def save_project(payload: ProjectPayload) -> dict:
    return create_project(payload)


@router.delete("/projects/{project_id}")
def remove_project(project_id: int) -> dict:
    if not delete_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found.")
    return {"deleted": True, "id": project_id}


@router.get("/experiments")
def experiments(project_id: int | None = None, limit: int = 100) -> dict:
    return {"experiments": list_experiments(project_id, max(1, min(limit, 500)))}


@router.post("/experiments")
def save_experiment(payload: ExperimentPayload) -> dict:
    try:
        return create_experiment(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="The experiment could not be saved.") from exc


@router.get("/models")
def models() -> dict:
    return {"models": list_models()}


@router.post("/models")
def add_model(payload: ModelRecordPayload) -> dict:
    try:
        return register_model(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="That model record already exists or is invalid.") from exc


@router.post("/reports")
def report(payload: ReportRequest) -> Response:
    content, media_type = generate_report(payload)
    suffix = "md" if payload.format == "markdown" else "html"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="marketforge-report.{suffix}"'},
    )


@router.post("/replications/analyse")
async def replication(
    file: UploadFile = File(...), settings_json: str = Form("{}")
) -> dict:
    settings = _parse_settings(settings_json, ReplicationRequest)
    _, content = await _read_upload_content(file)
    try:
        return await _run_heavy(analyse_external_replication, content, settings)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
