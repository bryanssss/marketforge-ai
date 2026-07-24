# MarketForge AI

> Version 0.4 includes the final-audit prospective v2 benchmark with deterministic CPU execution and a frozen software environment.

**MarketForge AI** is a local-first financial forecasting, data-validation and
walk-forward backtesting studio. It offers a polished browser interface without
requiring Node.js or npm.

> Research and educational software only. Nothing in this project is financial
> advice, a trading signal or a promise of profit.

## Why This Project Exists

The original Kronos project introduced an open-source foundation model for
financial candlesticks. MarketForge AI builds a broader product workflow around
that research:

- A new responsive interface
- Strict CSV and candle validation
- Automatic repair of impossible OHLC relationships
- Non-negative volume enforcement
- A transparent bootstrap baseline with uncertainty bands
- Optional Kronos Mini, Small and Base integration
- Chronological walk-forward backtesting
- Fees and slippage
- JSON result export
- Docker packaging
- Automated tests
- A pre-registered frozen benchmark with exact model/data revisions and statistical claim gates

The Kronos source and weights are **not bundled**. See
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

## Screens and Features

### Forecast Studio

Upload a CSV, select the future horizon and generate a median path with an
80% scenario range. When Kronos is installed, **Auto** attempts to use it;
otherwise the safe statistical baseline remains available.

### Data Quality Layer

MarketForge accepts these required columns:

```text
open, high, low, close
```

Optional columns:

```text
volume, timestamp
```

Common aliases such as `date`, `timestamps`, `o`, `h`, `l`, `c` and `vol` are
recognised. The application sorts timestamps, removes duplicates, discards
invalid rows and repairs impossible candles.

### Walk-Forward Backtesting

Each simulated decision only sees candles that existed before that decision.
The test supports a forecast threshold, fees and slippage. This is safer than
randomly mixing past and future rows, but it is still a research simulation.

## Run on Windows

1. Install Python 3.10 or newer.
2. Tick **Add Python to PATH** during Python installation.
3. Double-click `start_windows.bat`.
4. Open `http://127.0.0.1:7070` if the browser does not open automatically.

## Run on macOS or Linux

```bash
chmod +x start_mac_linux.sh
./start_mac_linux.sh
```

## Manual Start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

## Install Optional Kronos Support

Windows:

```text
scripts\install_kronos_windows.bat
```

macOS/Linux:

```bash
./scripts/install_kronos_mac_linux.sh
```

This downloads the official repository into `vendor/Kronos` and installs the
heavier machine-learning dependencies. Model weights are then downloaded by
Kronos from Hugging Face when first used.


## Prospective Frozen Benchmark v2

MarketForge 0.4 includes a prospective benchmark designed to answer one narrow question: does the frozen MarketForge ensemble produce lower terminal log-return error than the pinned Kronos Base comparator on future, matched market candles?

**Current status (24 July 2026): `PREREGISTERED — INCOMPLETE BY DESIGN`.** The holdout begins on 1 August 2026 and ends on 31 October 2026. Collection is blocked until 3 November 2026, after the final official monthly archives should be available. This release therefore contains no score and makes no superiority claim.

The final audit superseded v1 before the holdout began because `device: auto` could choose different hardware. V2 now freezes:

- CPU-only deterministic inference
- One numerical thread
- Python 3.11 and exact direct numerical/model dependencies
- Exact 00:00 UTC daily forecast origins
- Official provider archive and checksum-file hashes
- Canonical dataset hashes
- Kronos source, patch, model and tokenizer revisions
- Protocol, environment and prediction-ledger bindings
- A second full replay of every deterministic prediction before reporting

First create the dedicated benchmark environment:

Windows:

```text
scripts\setup_benchmark_env_windows.bat
```

macOS/Linux:

```bash
./scripts/setup_benchmark_env_mac_linux.sh
```

After 3 November 2026, run the matching `run_frozen_benchmark` script. The final decision is written to `benchmarks/frozen_v2/results/benchmark_report.md`. Read [`docs/FROZEN_BENCHMARK.md`](docs/FROZEN_BENCHMARK.md) before publishing any comparison claim.

## Docker

```bash
docker compose up --build
```

Then open `http://localhost:7070`.

## API

FastAPI documentation is available at:

```text
http://127.0.0.1:7070/docs
```

Main endpoints:

- `GET /api/health`
- `GET /api/sample`
- `POST /api/analyse`
- `POST /api/forecast`
- `POST /api/backtest`
- `POST /api/compare`

## Tests

```bash
pip install pytest
pytest -q --cov=app
```

GitHub Actions runs these tests automatically after every push.

## Publish on GitHub

Follow the very simple guide in
[`docs/GITHUB_FOR_BEGINNERS.md`](docs/GITHUB_FOR_BEGINNERS.md).

## What Is Original and What Is Third-Party?

MarketForge AI's interface, data pipeline, baseline engine, walk-forward test,
API, packaging and documentation are original parts of this repository.
Kronos remains a separate third-party open-source project created by its
respective authors. Its MIT licence and attribution must remain intact when it
is installed or redistributed.

## Licence

MarketForge AI is released under the MIT Licence. See [`LICENSE`](LICENSE).
Third-party components remain under their own licences.
