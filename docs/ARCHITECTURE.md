# Architecture

## Application Flow

```text
Browser / optional desktop shell
  │ CSV uploads, public market requests and validated settings
  ▼
FastAPI guardrails
  │ request size, type, host, concurrency and request ID
  ├──────────────────────────────────────────────────────────────┐
  ▼                                                              ▼
Data service                                               Public connectors
  │ aliases → UTC → finite values → OHLC repair                  │ Binance / Coinbase / Kraken
  │ gap report → quality score → fingerprint                     │ response normalisation
  ├───────────────┬──────────────────┬────────────────────────────┘
  ▼               ▼                  ▼
Forecasting       Research lab       Multi-asset and portfolio
  │               │                  │ alignment / returns / covariance
  │ baselines     ├─ regime          │ allocations / rebalance simulation
  │ calibration   ├─ volatility      │ drawdown / risk diagnostics
  │ optional      ├─ stress tests    │
  │ Kronos        └─ reports         │
  └───────────────┬──────────────────┘
                  ▼
          JSON, charts, tables and local exports
                  │
                  ▼
          SQLite research workspace
          projects / experiments / model records
```

## Primary Modules

- `app/services/data_service.py`: parsing, validation, repairs and provenance.
- `app/services/connectors_service.py`: read-only public market-data adapters.
- `app/services/forecast_service.py`: transparent models, calibration and Kronos adapter.
- `app/services/calibration_service.py`: empirical and conformal interval adjustments.
- `app/services/regime_service.py`: interpretable market-regime classification.
- `app/services/volatility_service.py`: EWMA, Parkinson and Garman–Klass estimates.
- `app/services/stress_service.py`: historical and synthetic shock analysis.
- `app/services/backtest_service.py`: chronological forecast and execution simulation.
- `app/services/comparison_service.py`: matched rolling-origin model leaderboard.
- `app/services/portfolio_service.py`: multi-asset alignment, allocation and simulation.
- `app/services/storage_service.py`: local SQLite projects, experiments and model metadata.
- `app/services/report_service.py`: Markdown research-report templates.
- `app/services/replication_service.py`: paired external-result analysis.
- `app/benchmark/`: frozen protocol, data, evidence, replay and statistics engine.
- `scripts/patch_kronos_compat.py`: verified, reversible third-party compatibility patch.
- `scripts/doctor.py`: local installation diagnostics.

## Storage Boundary

MarketForge stores project metadata locally in `storage/marketforge.db`. The database is
excluded from Git. It may contain filenames, settings and research notes, so users should
back it up and protect it like any other local research file.

The storage layer is intentionally metadata-oriented. Large datasets and model weights
are not embedded in the database.

## Connector Boundary

Connectors use public, read-only market-data endpoints. They do not require or accept
exchange secret keys and do not place orders. Remote responses are untrusted and pass
through the same validation pipeline as uploaded CSV files.

Provider availability, rate limits and historical coverage remain external constraints.
For immutable evidence, export and fingerprint the retrieved dataset.

## Desktop Boundary

`desktop.py` and the PyInstaller specification wrap the same local FastAPI application.
The desktop package is not a separate forecasting implementation. Platform-specific
executables must be built and tested on their target operating systems.

## Trust Boundaries

- Uploaded files and remote provider responses are untrusted.
- API settings are untrusted and validated by Pydantic.
- Project titles, notes and model metadata are escaped before browser display.
- Installed Kronos source is third-party and kept under `vendor/Kronos`.
- Kronos model weights are third-party and are not committed.
- A hosted deployment is not local processing; uploaded files reach that host.
- The local model registry records metadata and must not execute arbitrary code.
- External replication files are claims supplied by another party, not proof of independence.

## Extension Rules

A new forecasting engine should:

1. consume only the supplied historical context;
2. return scenario paths or a documented probabilistic distribution;
3. preserve valid OHLC relationships;
4. expose revision, settings and reproducibility metadata;
5. include a naive benchmark;
6. add tests for no future-data access;
7. never silently fall back to a different engine;
8. declare its calibration method;
9. remain outside a frozen protocol unless a new benchmark is preregistered.

A new connector should:

1. use read-only public endpoints;
2. declare symbol and interval rules;
3. enforce timeouts and response-size limits;
4. normalise to canonical UTC OHLCV columns;
5. pass through the ordinary validation service;
6. include parser tests using recorded synthetic payloads;
7. avoid collecting credentials.
