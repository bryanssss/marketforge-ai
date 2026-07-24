# Upgrade an Existing Repository to MarketForge AI 0.5

## Before Replacing Files

1. Commit or back up your existing repository.
2. Close MarketForge if it is running.
3. Copy `storage/marketforge.db` somewhere safe when you already have saved local work.
4. Do not copy a downloaded `vendor/Kronos` folder into Git.

## Upgrade

1. Extract the MarketForge AI 0.5 ZIP.
2. Copy all files into the existing local `marketforge-ai` repository.
3. Choose **Replace files in the destination**.
4. Restore your private `storage/marketforge.db` only on your computer, never in Git.
5. Delete the old `.venv` when dependency installation behaves unexpectedly.
6. Start MarketForge again so the application can create or update local storage tables.

## Verify

```bash
python -m compileall -q app tests scripts run.py desktop.py
pytest -q --cov=app --cov-fail-under=78
node --check app/static/app.js
python scripts/benchmark.py status
```

Expected benchmark identifier:

```text
marketforge-prospective-v3
```

## Commit

Suggested commit message:

```text
Release MarketForge AI 0.5 research workbench
```

Wait for the newest GitHub Actions to pass before creating tag `v0.5.0`.
