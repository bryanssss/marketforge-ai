# Contributing

1. Create a focused branch from `main`.
2. Keep behavioural changes small enough to review.
3. Add or update tests for every bug fix and new code path.
4. Run the checks below before opening a pull request.
5. Do not commit model weights, virtual environments, private market data,
   credentials or generated benchmark results containing unreviewed evidence.
6. Explain what changed, why it is correct and how it was tested.

```bash
python -m compileall -q app tests scripts run.py
ruff check .
pytest -q --cov=app --cov-fail-under=78
node --check app/static/app.js
python scripts/benchmark.py status
```

## Frozen benchmark rule

The v2 preregistration seal binds the benchmark specification and relevant
source files. Do not edit a bound file and then replace the existing seal. A
methodological change requires a new benchmark directory and identifier while
keeping the old protocol available for auditability.

## Research claims

A pull request that changes forecasting or evaluation must report all relevant
baselines, failed configurations and limitations. A prettier chart or higher
backtest return alone is not evidence of superior forecasting.
