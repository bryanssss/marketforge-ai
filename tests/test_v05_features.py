from __future__ import annotations

import io
import json

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from app.core.schemas import (
    ConnectorRequest,
    ForecastSettings,
    PortfolioSettings,
    ReplicationRequest,
    ReportRequest,
    StressSettings,
    VolatilitySettings,
)
from app.main import app
from app.services.connectors_service import import_market_data
from app.services.forecast_service import baseline_forecast
from app.services.portfolio_service import analyse_multi_asset, run_portfolio_simulation
from app.services.regime_service import classify_market_regime
from app.services.replication_service import analyse_external_replication
from app.services.report_service import generate_report
from app.services.stress_service import run_stress_test
from app.services.volatility_service import forecast_volatility

client = TestClient(app)


def test_all_new_baseline_models_are_valid(market_df: pd.DataFrame) -> None:
    for model in ("exponential_smoothing", "momentum", "mean_reversion", "regime_ensemble"):
        result = baseline_forecast(
            market_df,
            ForecastSettings(
                engine="baseline",
                baseline_model=model,
                horizon=6,
                lookback=120,
                paths=30,
                block_size=4,
                seed=9,
                calibration="conformal",
            ),
        )
        assert len(result.forecast) == 6
        assert (result.forecast["upper_close"] >= result.forecast["lower_close"]).all()
        assert result.summary["regime"]
        assert result.metadata["calibration"]["method"] == "conformal"


def test_regime_volatility_and_stress_services(market_df: pd.DataFrame) -> None:
    regime = classify_market_regime(market_df, 120)
    assert regime["regime"]
    assert 0 <= regime["confidence"] <= 1

    volatility = forecast_volatility(
        market_df,
        VolatilitySettings(method="ensemble", horizon=12, lookback=100),
    )
    assert volatility["horizon_volatility_percent"] >= 0
    assert set(volatility["component_estimates_percent"]) == {"ewma", "parkinson", "garman_klass"}

    stress = run_stress_test(
        market_df,
        StressSettings(price_shock_percent=-12, volatility_multiplier=2.5, scenarios=500),
    )
    assert stress["scenarios"] == 500
    assert 0 <= stress["loss_probability_percent"] <= 100


def test_portfolio_and_multi_asset_analysis(market_df: pd.DataFrame) -> None:
    second = market_df.copy()
    second["close"] *= np.exp(np.linspace(0, 0.08, len(second)))
    second["open"] *= np.exp(np.linspace(0, 0.08, len(second)))
    second["high"] = np.maximum(second["high"], np.maximum(second["open"], second["close"]))
    second["low"] = np.minimum(second["low"], np.minimum(second["open"], second["close"]))
    datasets = {"asset_a": market_df, "asset_b": second}
    analysis = analyse_multi_asset(datasets)
    assert analysis["matched_rows"] == len(market_df)
    assert analysis["correlation"]["asset_a"]["asset_a"] == 1.0

    result = run_portfolio_simulation(
        datasets,
        PortfolioSettings(
            allocation="risk_parity",
            lookback=60,
            rebalance_every=24,
            max_weight_percent=80,
        ),
    )
    assert result["metrics"]["rebalances"] > 0
    assert abs(sum(result["latest_weights"].values()) - 100) < 0.01


def test_public_connector_normalises_binance_payload() -> None:
    payload = [
        [1704067200000 + index * 3600000, "100", "103", "99", "102", "5", 0, "510", 0, 0, 0, 0]
        for index in range(45)
    ]
    dataframe, report, metadata = import_market_data(
        ConnectorRequest(exchange="binance", symbol="BTCUSDT", interval="1h", limit=45),
        fetcher=lambda _: payload,
    )
    assert len(dataframe) == 45
    assert report.quality_score >= 90
    assert metadata["connector"]["id"] == "binance"


def test_report_templates_and_external_replication() -> None:
    markdown, media = generate_report(
        ReportRequest(
            template="risk",
            title="Risk Test",
            result={"metrics": {"max_drawdown_percent": -12.3}, "notes": ["Example"]},
        )
    )
    assert media.startswith("text/markdown")
    assert "# Risk Test" in markdown
    assert "Max Drawdown Percent" in markdown

    origins = pd.date_range("2026-01-01", periods=20, freq="D", tz="UTC")
    rows = []
    for index, origin in enumerate(origins):
        actual = 100 + index
        rows.append({"origin": origin, "model": "candidate", "actual": actual, "prediction": actual * 1.001})
        rows.append({"origin": origin, "model": "comparator", "actual": actual, "prediction": actual * 1.01})
    content = pd.DataFrame(rows).to_csv(index=False).encode()
    result = analyse_external_replication(
        content,
        ReplicationRequest(candidate_name="candidate", comparator_name="comparator", bootstrap_samples=300),
    )
    assert result["matched_origins"] == 20
    assert result["relative_improvement_percent"] > 0


def test_v05_api_lab_portfolio_and_reports(market_csv: bytes) -> None:
    regime = client.post("/api/regime", files={"file": ("market.csv", market_csv, "text/csv")})
    assert regime.status_code == 200
    assert regime.json()["regime"]

    volatility = client.post(
        "/api/volatility",
        files={"file": ("market.csv", market_csv, "text/csv")},
        data={"settings_json": json.dumps({"lookback": 80, "horizon": 6})},
    )
    assert volatility.status_code == 200

    stress = client.post(
        "/api/stress",
        files={"file": ("market.csv", market_csv, "text/csv")},
        data={"settings_json": json.dumps({"scenarios": 200})},
    )
    assert stress.status_code == 200

    portfolio = client.post(
        "/api/portfolio",
        files=[
            ("files", ("a.csv", market_csv, "text/csv")),
            ("files", ("b.csv", market_csv, "text/csv")),
        ],
        data={"settings_json": json.dumps({"lookback": 60, "rebalance_every": 24})},
    )
    assert portfolio.status_code == 200
    assert portfolio.json()["metrics"]["rebalances"] > 0

    report = client.post(
        "/api/reports",
        json={"template": "executive", "title": "API Report", "result": {"summary": {"value": 1}}},
    )
    assert report.status_code == 200
    assert "API Report" in report.text


def test_connector_list_and_model_registry_endpoints() -> None:
    connectors = client.get("/api/connectors")
    assert connectors.status_code == 200
    assert {item["id"] for item in connectors.json()["connectors"]} == {"binance", "coinbase", "kraken"}
    models = client.get("/api/models")
    assert models.status_code == 200
    assert len(models.json()["models"]) >= 7


def test_replication_endpoint() -> None:
    rows = []
    for index in range(12):
        origin = f"2026-01-{index + 1:02d}T00:00:00Z"
        rows.append([origin, "candidate", 100 + index, 100 + index + 0.1])
        rows.append([origin, "comparator", 100 + index, 100 + index + 1.0])
    frame = pd.DataFrame(rows, columns=["origin", "model", "actual", "prediction"])
    buffer = io.BytesIO(frame.to_csv(index=False).encode())
    response = client.post(
        "/api/replications/analyse",
        files={"file": ("ledger.csv", buffer.getvalue(), "text/csv")},
        data={"settings_json": json.dumps({"bootstrap_samples": 200, "block_size": 2})},
    )
    assert response.status_code == 200
    assert response.json()["matched_origins"] == 12


def test_public_connector_normalises_coinbase_payload() -> None:
    payload = [
        [1704067200 + index * 3600, "99", "103", "100", "102", "5"]
        for index in range(45)
    ]
    dataframe, report, metadata = import_market_data(
        ConnectorRequest(exchange="coinbase", symbol="BTC-USD", interval="1h", limit=45),
        fetcher=lambda _: payload,
    )
    assert len(dataframe) == 45
    assert report.quality_score >= 90
    assert metadata["connector"]["id"] == "coinbase"


def test_public_connector_normalises_kraken_payload() -> None:
    candles = [
        [1704067200 + index * 3600, "100", "103", "99", "102", "101", "5", 10]
        for index in range(45)
    ]
    payload = {"error": [], "result": {"XXBTZUSD": candles, "last": "1704225600"}}
    dataframe, report, metadata = import_market_data(
        ConnectorRequest(exchange="kraken", symbol="XBTUSD", interval="1h", limit=45),
        fetcher=lambda _: payload,
    )
    assert len(dataframe) == 45
    assert report.quality_score >= 90
    assert metadata["connector"]["id"] == "kraken"


def test_local_projects_experiments_and_model_registry(tmp_path, monkeypatch) -> None:
    from app.core.schemas import ExperimentPayload, ModelRecordPayload, ProjectPayload
    from app.services import storage_service

    monkeypatch.setattr(storage_service, "_DB_PATH", tmp_path / "marketforge.db")
    project = storage_service.create_project(
        ProjectPayload(
            name="Test project",
            description="Local research workspace",
            settings={"engine": "baseline"},
            dataset_fingerprints=["abc123"],
            language="en",
        )
    )
    assert project["name"] == "Test project"
    assert storage_service.list_projects()[0]["settings"]["engine"] == "baseline"

    experiment = storage_service.create_experiment(
        ExperimentPayload(
            project_id=project["id"],
            name="Test experiment",
            kind="forecast",
            dataset_fingerprint="abc123",
            settings={"horizon": 6},
            metrics={"mae": 0.01},
            result={"forecast": [1, 2, 3]},
            tags=["test"],
        )
    )
    assert len(experiment["result_hash"]) == 64
    assert storage_service.list_experiments(project["id"])[0]["metrics"]["mae"] == 0.01

    model = storage_service.register_model(
        ModelRecordPayload(
            name="External metadata only",
            family="research",
            version="1",
            source="https://example.invalid/model",
            revision="abc",
            checksum="123",
            metadata={"execution_allowed": False},
            active=False,
        )
    )
    assert model["active"] is False
    assert any(item["name"] == "External metadata only" for item in storage_service.list_models())
    assert storage_service.delete_project(project["id"]) is True
