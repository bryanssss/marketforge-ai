# Contributing

Thank you for helping improve MarketForge AI.

## Development Workflow

1. Create a focused branch from `main`.
2. Keep behavioural changes small enough to review.
3. Add or update tests for every bug fix and new code path.
4. Explain what changed, why it is correct and how it was tested.
5. Do not commit model weights, virtual environments, private market data, credentials,
   local SQLite databases or unreviewed benchmark results.

Run the standard checks before opening a pull request:

```bash
python -m compileall -q app tests scripts run.py desktop.py
ruff check app run.py --select E9,F63,F7,F82
pytest -q --cov=app --cov-fail-under=78
node --check app/static/app.js
python scripts/benchmark.py status
```

## Feature Contributions

New forecasting models should include:

- a plain-language method description;
- deterministic seed handling where applicable;
- valid OHLC output guarantees;
- uncertainty or calibration metadata;
- a matched comparison with the naive baseline;
- tests for chronological data use.

New public connectors should include:

- official provider documentation;
- no trading or credential handling;
- timeout and size limits;
- parser tests with synthetic or recorded response shapes;
- canonical UTC OHLCV output.

New report templates, translations and accessibility improvements should be usable without
changing benchmark logic.

## Frozen Benchmark Rule

Prospective v3 binds its specification, model lock and relevant source files. Do not edit
a bound file and replace the existing seal. A methodological or candidate-model change
requires a new benchmark directory and identifier while preserving v3 for auditability.

Versions 1 and 2 remain historical records and must not be rewritten.

## Research Claims

A pull request that changes forecasting or evaluation must report relevant baselines,
failed configurations, limitations and leakage risks. A prettier chart or a higher
historical backtest return is not evidence of superior forecasting.
