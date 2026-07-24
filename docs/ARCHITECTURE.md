# Architecture

## Request Flow

```text
Browser
  │ multipart CSV + validated settings
  ▼
FastAPI guardrails
  │ size / type / host / request ID
  ▼
Data service
  │ aliases → UTC → finite values → OHLC repair → gap report → fingerprint
  ├──────────────────────────────┐
  ▼                              ▼
Forecast service                 Backtest service
  │                              │ rolling origin
  ├─ transparent baselines       │ later-open execution
  └─ optional Kronos adapter     │ costs / stops / no overlap
          │                      │
          ▼                      ▼
Validated scenario quantiles   forecast + strategy evidence
          └──────────────┬───────┘
                         ▼
                  JSON + browser charts
```

## Trust Boundaries

- Uploaded files are untrusted.
- Settings are untrusted and validated by Pydantic.
- Installed Kronos source is third-party and kept under `vendor/Kronos`.
- Kronos model weights are third-party and are not committed.
- Browser output escapes uploaded names and server-provided text.
- Hosted deployment is not local processing; files reach the host.

## Important Modules

- `app/services/data_service.py`: parsing, validation and provenance.
- `app/services/forecast_service.py`: baselines, Kronos cache and uncertainty.
- `app/services/backtest_service.py`: chronological forecast and execution simulator.
- `app/services/comparison_service.py`: matched rolling-origin model leaderboard.
- `scripts/patch_kronos_compat.py`: verified, reversible third-party compatibility patch.
- `scripts/doctor.py`: installation diagnostics.

## Extension Rules

A new forecasting engine should:

1. consume only the supplied historical context;
2. return several scenario paths or a documented probabilistic distribution;
3. preserve valid OHLC relationships;
4. expose revision and reproducibility metadata;
5. include a naive benchmark;
6. add tests for no future-data access;
7. never silently fall back to a different engine.
