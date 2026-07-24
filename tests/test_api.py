from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_and_security_headers() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["version"] == "0.5.0"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-request-id"]


def test_forecast_endpoint(market_csv: bytes) -> None:
    settings = {
        "engine": "baseline",
        "baseline_model": "ensemble",
        "horizon": 8,
        "lookback": 100,
        "paths": 20,
        "block_size": 4,
    }
    response = client.post(
        "/api/forecast",
        files={"file": ("market.csv", market_csv, "text/csv")},
        data={"settings_json": json.dumps(settings)},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["engine"] == "baseline-ensemble"
    assert len(payload["forecast"]) == 8
    assert payload["data_report"]["quality_score"] >= 90


def test_backtest_endpoint(market_csv: bytes) -> None:
    settings = {
        "baseline_model": "naive",
        "horizon": 4,
        "lookback": 80,
        "step": 20,
        "paths": 20,
        "block_size": 4,
    }
    response = client.post(
        "/api/backtest",
        files={"file": ("market.csv", market_csv, "text/csv")},
        data={"settings_json": json.dumps(settings)},
    )
    assert response.status_code == 200
    assert response.json()["forecast_metrics"]["evaluations"] > 0


def test_rejects_wrong_extension_and_invalid_settings(market_csv: bytes) -> None:
    wrong = client.post(
        "/api/forecast",
        files={"file": ("market.exe", market_csv, "text/csv")},
    )
    assert wrong.status_code == 400

    invalid = client.post(
        "/api/forecast",
        files={"file": ("market.csv", market_csv, "text/csv")},
        data={"settings_json": '{"horizon": 0}'},
    )
    assert invalid.status_code == 400
    assert "greater than or equal" in invalid.json()["detail"]


def test_request_size_guardrail() -> None:
    response = client.get("/api/health", headers={"content-length": "999999999"})
    assert response.status_code == 413


def test_compare_endpoint(market_csv: bytes) -> None:
    settings = {
        "models": ["naive", "drift"],
        "horizon": 4,
        "lookback": 80,
        "step": 40,
        "paths": 20,
        "block_size": 4,
    }
    response = client.post(
        "/api/compare",
        files={"file": ("market.csv", market_csv, "text/csv")},
        data={"settings_json": json.dumps(settings)},
    )
    assert response.status_code == 200
    assert len(response.json()["ranking"]) == 2
