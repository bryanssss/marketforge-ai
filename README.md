# MarketForge AI

[![Quality checks](https://github.com/bryanssss/marketforge-ai/actions/workflows/tests.yml/badge.svg)](https://github.com/bryanssss/marketforge-ai/actions/workflows/tests.yml)
[![CodeQL](https://github.com/bryanssss/marketforge-ai/actions/workflows/codeql.yml/badge.svg)](https://github.com/bryanssss/marketforge-ai/actions/workflows/codeql.yml)
[![Licence: MIT](https://img.shields.io/badge/Licence-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Powered-009688.svg)](https://fastapi.tiangolo.com/)
[![Status](https://img.shields.io/badge/Status-Research%20Alpha-orange.svg)](#project-status)
[![Privacy](https://img.shields.io/badge/Privacy-Local--First-6366f1.svg)](#privacy-and-security)

[![Support MarketForge AI](https://img.shields.io/badge/Support%20MarketForge%20AI-Donate%20with%20PayPal-0070ba?style=for-the-badge&logo=paypal&logoColor=white)](https://www.paypal.com/donate/?hosted_button_id=YE9H5NCNLWU38)

**MarketForge AI** is a local-first market forecasting, data-quality, portfolio simulation and reproducible research studio.

It imports OHLCV candles from CSV files or public exchange endpoints, generates probabilistic forecasts, compares transparent forecasting models, evaluates chronological strategies, analyses multiple assets, forecasts volatility, classifies market regimes, runs stress scenarios and saves research evidence locally.

The standard application requires Python but does **not** require Node.js, npm, registration or a hosted application server. Optional Kronos support and optional desktop packaging can be installed separately.

> **Research and educational software only.** MarketForge AI does not provide financial advice, guaranteed predictions, automated trading signals or promises of profit.

---

## Table of Contents

- [What Is New in Version 0.5](#what-is-new-in-version-05)
- [Why MarketForge Exists](#why-marketforge-exists)
- [Core Features](#core-features)
- [Forecasting Models](#forecasting-models)
- [Direct Exchange Imports](#direct-exchange-imports)
- [Portfolio and Multi-Asset Research](#portfolio-and-multi-asset-research)
- [Research Lab](#research-lab)
- [Projects, Experiments and Model Registry](#projects-experiments-and-model-registry)
- [Reports and External Replication](#reports-and-external-replication)
- [Prospective Frozen Benchmark v3](#prospective-frozen-benchmark-v3)
- [Quick Start](#quick-start)
- [Optional Kronos Support](#optional-kronos-support)
- [Desktop Packaging](#desktop-packaging)
- [CSV Format](#csv-format)
- [Docker](#docker)
- [API](#api)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Privacy and Security](#privacy-and-security)
- [Research Limitations](#research-limitations)
- [Project Status](#project-status)
- [Contributing](#contributing)
- [Support This Free Project](#support-this-free-project)
- [Third-Party Components](#third-party-components)
- [Licence](#licence)

---

## What Is New in Version 0.5

Version 0.5 turns the earlier forecasting application into a broader research workbench.

### New market-data tools

- Public Binance Spot candle imports
- Public Coinbase Exchange candle imports
- Public Kraken Spot candle imports
- Exchange-specific intervals and limits
- Imported data passes through the same validation pipeline as uploaded CSV files

### New forecasting and evidence tools

- Exponential-smoothing forecast model
- Momentum forecast model
- Mean-reversion forecast model
- Regime-aware ensemble
- Empirical interval calibration
- Widen-only conformal interval calibration
- Market-regime classification
- EWMA, Parkinson and Garman–Klass volatility estimates
- Scenario stress testing
- Expanded backtest diagnostics

### New portfolio tools

- Multi-asset correlation analysis
- Equal-weight allocation
- Inverse-volatility allocation
- Risk-parity allocation
- Minimum-variance allocation
- Rebalancing frequency controls
- Position-weight limits
- Turnover and fee modelling
- Portfolio equity and drawdown analysis

### New research-management tools

- Saved local projects
- Experiment history with result hashes
- Local model registry
- Executive, research, risk and model-card reports
- Standard external benchmark-replication ledger analyser
- English, Bulgarian and Spanish interface foundations
- High-contrast mode
- Reduced-motion support
- Keyboard focus improvements
- Accessible chart-data tables
- Optional desktop executable packaging

The complete change history is in [`CHANGELOG.md`](CHANGELOG.md).

---

## Why MarketForge Exists

The original [Kronos project](https://github.com/shiyu-coder/Kronos) introduced an open-source foundation model for financial candlestick data.

A forecasting model alone is not a complete research workflow. Responsible evaluation also needs:

- Reliable data validation
- Simple reference models
- Clear uncertainty intervals
- Chronological evaluation
- Realistic execution timing
- Fees and slippage
- Portfolio risk analysis
- Reproducible model revisions
- Statistical confidence testing
- Clear research limitations

MarketForge adds these application and research layers while keeping Kronos optional and separately attributed.

The Kronos source code and model weights are not bundled. See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

---

## Core Features

### Local-first browser studio

The normal application runs on your computer at:

```text
http://127.0.0.1:7070
```

Local mode does not upload CSV files to a MarketForge service. A hosted deployment processes files on whichever server you deploy.

### Data-quality pipeline

MarketForge checks for:

- Missing required OHLC fields
- Invalid or non-positive prices
- Impossible candle relationships
- Duplicate timestamps
- Out-of-order rows
- Negative volume or amount
- Irregular time intervals
- Estimated missing candles
- Large return outliers
- Oversized or binary uploads

Normal application mode can repair selected malformed values and reports every change. Frozen benchmark mode rejects invalid source data instead of silently repairing it.

### Forecast studio

The forecast screen provides:

- Configurable lookback and horizon
- Reproducible seeds
- Multiple generated paths
- Median forecast
- Central uncertainty range
- Optional calibration
- Market-regime summary
- JSON export
- Accessible table representation
- Adjustable visible chart history

### Walk-forward backtesting

Each simulated decision sees only historical candles available before the signal. Entries occur at a later candle open rather than at a price already used to generate the signal.

Controls include:

- Forecast threshold
- Long-only, short-only or long/short mode
- Fees and slippage
- Position size
- Execution delay
- Stop loss
- Take profit
- Optional overlapping positions

Forecast accuracy is reported separately from trade performance.

---

## Forecasting Models

MarketForge includes eight transparent baseline choices:

| Model | Purpose |
|---|---|
| `naive` | Near-persistence reference model |
| `drift` | Robust recent drift with stochastic shocks |
| `block_bootstrap` | Resamples consecutive candle patterns |
| `exponential_smoothing` | Emphasises recent returns with decaying weights |
| `momentum` | Extends weighted recent direction with decay |
| `mean_reversion` | Pulls price towards an exponential anchor |
| `ensemble` | General blend of block, drift and naive paths |
| `regime_ensemble` | Selects a transparent model mixture based on the current regime |

Optional Kronos Mini, Small and Base models can be installed separately.

A complex model should not be preferred simply because it sounds more advanced. Use matched historical dates, repeat seeds and a later untouched period.

---

## Direct Exchange Imports

The browser interface can import recent public candles from:

- Binance Spot
- Coinbase Exchange
- Kraken Spot

No trading permission or private API key is requested. The connectors are read-only and use fixed official market-data hosts.

Provider limits differ. MarketForge displays connector-specific intervals and maximum recent candle counts.

Imported candles are converted into a normal CSV object inside the browser and then use the same validation and forecasting workflow as a manually uploaded file.

> Public endpoint availability, symbol names, regional access and rate limits are controlled by each provider.

---

## Portfolio and Multi-Asset Research

Select between two and twenty CSV files to analyse assets on their matching timestamps.

### Multi-asset diagnostics

- Correlation matrix
- Per-asset return
- Per-asset volatility
- Matching date range
- Equal-weight diversification ratio

### Allocation methods

- Equal weight
- Inverse volatility
- Risk parity
- Minimum variance

### Portfolio simulation controls

- Trailing allocation lookback
- Rebalance frequency
- Minimum and maximum weights
- Transaction fee assumption
- Initial capital
- Optional target volatility

### Portfolio results

- Final equity
- Total return
- Maximum drawdown
- Per-candle volatility
- Sharpe-style ratio
- Sortino-style ratio
- Total turnover
- Weight history
- Latest allocation

This remains a research simulation and does not model every live execution constraint.

---

## Research Lab

### Market-regime classification

The regime tool describes the current window as one of several transparent states, including:

- Uptrend
- Downtrend
- Sideways
- High-volatility trend
- Low-volatility sideways market
- Liquidity shock

It also reports trend strength, recent return, volatility percentile and downside/upside volatility asymmetry.

### Volatility forecasting

Available estimators:

- EWMA close-return variance
- Parkinson high/low estimator
- Garman–Klass OHLC estimator
- Ensemble average

The result includes per-candle, horizon and annualised volatility estimates.

### Scenario stress testing

Stress controls include:

- Immediate price shock
- Volatility multiplier
- Liquidity cost
- Number of simulated scenarios
- Reproducible seed

Outputs include loss probability, expected stressed return, value at risk, expected shortfall and return percentiles.

---

## Projects, Experiments and Model Registry

MarketForge creates a local SQLite database under:

```text
storage/marketforge.db
```

The folder is excluded from Git by default.

### Saved projects

Projects can record:

- Name and description
- Interface language
- Research settings
- Dataset fingerprints
- Creation and update timestamps

### Experiment tracking

Saved experiments include:

- Experiment type
- Dataset fingerprint
- Settings
- Metrics
- Result payload
- Tags
- SHA-256 result hash
- Creation timestamp

### Model registry

The local model registry stores:

- Model name and family
- Version
- Source
- Revision
- Checksum
- Metadata
- Active status

The registry records model identity; registering metadata does not automatically execute arbitrary third-party model code.

---

## Reports and External Replication

### Report templates

MarketForge can generate downloadable Markdown or HTML reports using:

- Executive summary
- Research report
- Risk report
- Model card

Reports include key metrics, evidence notes, settings and limitations.

### Independent external replication

The external replication analyser accepts a standard CSV prediction ledger:

```csv
origin,model,actual,prediction
2026-01-01T00:00:00Z,candidate,101.0,100.7
2026-01-01T00:00:00Z,comparator,101.0,100.2
```

It calculates paired terminal log-return errors, a Diebold–Mariano comparison and a moving-block bootstrap confidence interval.

See [`docs/EXTERNAL_REPLICATION.md`](docs/EXTERNAL_REPLICATION.md).

---

## Prospective Frozen Benchmark v3

MarketForge 0.5 introduces **Prospective Frozen Benchmark v3** because the forecasting engine changed after v2 was publicly preregistered.

Version 2 remains preserved as a historical audit record. The current v3 protocol was sealed before the future holdout starts.

### Registered question

> Does the frozen MarketForge regime-aware ensemble produce lower terminal log-return error than the pinned Kronos Base comparator on future, matched market candles?

### Current status

```text
PREREGISTERED — INCOMPLETE BY DESIGN
```

### Holdout

```text
Start:       1 August 2026
End:         31 October 2026
Collection:  3 November 2026 or later
```

### Registered assets and horizons

- BTC/USDT
- ETH/USDT
- BNB/USDT
- SOL/USDT
- XRP/USDT
- 1-hour candles
- 1-hour, 6-hour and 24-hour horizons

### Frozen execution

- CPU-only deterministic inference
- One numerical thread
- Python 3.11
- Exact dependency versions
- Exact 00:00 UTC origins
- Exact model and tokenizer revisions
- Frozen empirical interval calibration
- Official provider archive checksums
- Canonical dataset hashes
- Prediction-ledger hash chain
- Full deterministic replay
- Statistical claim gate

The current v3 seal is stored in:

```text
benchmarks/frozen_v3/preregistration_lock.json
```

Run:

```bash
python scripts/benchmark.py status
```

Do not modify benchmark-bound Python code or lock files under the same benchmark ID. A methodological change requires a new benchmark version.

Read [`docs/FROZEN_BENCHMARK.md`](docs/FROZEN_BENCHMARK.md) before publishing any comparison claim.

---

## Quick Start

### Windows

1. Install Python 3.10 or newer.
2. Enable **Add Python to PATH**.
3. Extract the repository ZIP.
4. Double-click:

```text
start_windows.bat
```

### macOS or Linux

```bash
chmod +x start_mac_linux.sh
./start_mac_linux.sh
```

### Manual start

```bash
git clone https://github.com/bryanssss/marketforge-ai.git
cd marketforge-ai
python -m venv .venv
```

Activate the environment:

```bash
# Windows Command Prompt
.venv\Scripts\activate.bat

# macOS/Linux
source .venv/bin/activate
```

Install and start:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
python run.py
```

Open:

```text
http://127.0.0.1:7070
```

---

## Optional Kronos Support

### Windows

```text
scripts\install_kronos_windows.bat
```

### macOS or Linux

```bash
chmod +x scripts/install_kronos_mac_linux.sh
./scripts/install_kronos_mac_linux.sh
```

The installer downloads a pinned official Kronos source revision into `vendor/Kronos`, installs the larger machine-learning dependencies and applies the documented compatibility patch when required.

Model weights are downloaded from Hugging Face when first used and are not committed to this repository.

---

## Desktop Packaging

Version 0.5 includes optional PyWebView and PyInstaller packaging.

### Windows

```text
scripts\build_desktop_windows.bat
```

### macOS or Linux

```bash
./scripts/build_desktop_mac_linux.sh
```

The generated application appears under `dist/`.

Desktop packaging depends on operating-system webview components and must be tested on the target platform before distribution.

---

## CSV Format

Required columns:

```text
open, high, low, close
```

Recommended columns:

```text
timestamp, volume, amount
```

Example:

```csv
timestamp,open,high,low,close,volume
2026-01-01T00:00:00Z,42000,42450,41800,42250,1250.4
2026-01-01T01:00:00Z,42250,42600,42100,42520,1184.7
```

Common aliases such as `date`, `datetime`, `o`, `h`, `l`, `c`, `vol` and `turnover` are recognised.

---

## Docker

```bash
docker compose up --build
```

Open:

```text
http://localhost:7070
```

The container runs as a non-root user with a health check, dropped capabilities and a read-only filesystem configuration.

---

## API

Interactive documentation:

```text
http://127.0.0.1:7070/docs
```

Main endpoints include:

```text
GET    /api/health
GET    /api/engines
GET    /api/connectors
POST   /api/import-market-data
POST   /api/analyse
POST   /api/forecast
POST   /api/backtest
POST   /api/compare
POST   /api/regime
POST   /api/volatility
POST   /api/stress
POST   /api/multi-asset
POST   /api/portfolio
GET    /api/projects
POST   /api/projects
DELETE /api/projects/{id}
GET    /api/experiments
POST   /api/experiments
GET    /api/models
POST   /api/models
POST   /api/reports
POST   /api/replications/analyse
```

---

## Testing

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

Run tests and coverage:

```bash
pytest -q --cov=app --cov-report=term-missing --cov-fail-under=78
```

Additional checks:

```bash
python -m compileall -q app tests scripts run.py desktop.py
node --check app/static/app.js
python scripts/benchmark.py status
```

GitHub Actions runs tests across Python 3.10, 3.11, 3.12 and 3.13, plus CodeQL, dependency auditing and frozen benchmark smoke checks.

---

## Project Structure

```text
marketforge-ai/
├── app/
│   ├── api/                  # FastAPI routes
│   ├── benchmark/            # Frozen benchmark engine
│   ├── core/                 # Settings and schemas
│   ├── services/             # Forecast, portfolio, storage and research services
│   └── static/               # Browser interface
├── benchmarks/
│   ├── frozen_v1/            # Superseded audit record
│   ├── frozen_v2/            # Published v0.4 audit record
│   └── frozen_v3/            # Official v0.5 prospective protocol
├── data/                     # Sample data
├── docs/                     # Technical documentation
├── replication/              # External ledger example
├── scripts/                  # Install, build and benchmark tools
├── tests/                    # Automated test suite
├── desktop.py                # Optional desktop launcher
├── marketforge-desktop.spec  # PyInstaller specification
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-desktop.txt
├── requirements-kronos.txt
├── requirements-benchmark.txt
└── run.py
```

---

## Privacy and Security

MarketForge includes:

- Fixed-host public exchange connectors
- Upload and request-size limits
- Dataset row and column limits
- Trusted-host validation
- Sanitised server errors
- Content Security Policy
- Clickjacking protection
- MIME-sniffing protection
- Restricted browser permissions
- No-store API responses
- Heavy-job concurrency limits
- Local SQLite storage
- Non-root Docker execution
- Dependency auditing
- CodeQL analysis

Never commit:

- Exchange API keys
- Passwords
- Wallet secrets
- Private account statements
- Personal trading histories
- `.env` files
- Downloaded model weights
- `storage/marketforge.db`
- Confidential datasets

Read [`SECURITY.md`](SECURITY.md) before deploying publicly.

---

## Research Limitations

MarketForge cannot eliminate the fundamental uncertainty of financial markets.

Important limitations include:

- Market relationships can disappear.
- Models can fail during new regimes.
- Public model training boundaries may be uncertain.
- Historical simulations differ from live execution.
- Forecast intervals can be miscalibrated.
- Statistical significance does not guarantee profitability.
- Portfolio covariance estimates are unstable.
- Stress scenarios are assumptions, not predictions.
- Public exchange data can contain gaps or provider-specific conventions.
- A successful benchmark does not prove universal superiority.

Always verify data provenance, timestamps, model revisions, cost assumptions and evaluation independence.

---

## Project Status

MarketForge AI is an **alpha research release**.

Implemented features are functional and tested, but the project is not a regulated trading product and should not be used as the sole basis for financial decisions.

The prospective benchmark is preregistered but has not yet reached its future evaluation period. No claim is currently made that MarketForge is more accurate than Kronos.

See [`ROADMAP.md`](ROADMAP.md) for the next development phase.

---

## Contributing

Contributions are welcome in areas such as:

- Bug fixes
- Tests
- Data connectors
- Transparent forecast models
- Accessibility
- Documentation
- Portfolio diagnostics
- Security hardening
- External replication

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) before opening a pull request.

Do not silently modify the official v3 benchmark. Benchmark changes require a new identifier and preregistration.

---

## Support This Free Project

MarketForge AI is free and open-source research software.

Donations help support:

- Continued development
- Testing and security improvements
- Documentation
- Accessibility
- New transparent forecasting models
- Independent benchmark research
- Development and hosting costs

Donations are optional and do not purchase financial advice, recommendations, signals or guaranteed results.

[![Donate securely with PayPal](https://img.shields.io/badge/Donate%20securely%20with-PayPal-0070ba?style=for-the-badge&logo=paypal&logoColor=white)](https://www.paypal.com/donate/?hosted_button_id=YE9H5NCNLWU38)

**[Support MarketForge AI with PayPal](https://www.paypal.com/donate/?hosted_button_id=YE9H5NCNLWU38)**

Thank you for supporting independent open-source development and responsible forecasting research.

---

## Third-Party Components

Kronos was created by its respective authors and remains a separate third-party open-source project.

MarketForge does not claim ownership of:

- The Kronos architecture
- The Kronos tokenizer
- Kronos pretrained weights
- Original Kronos research
- Third-party datasets used to train Kronos

See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

---

## Licence

MarketForge AI is released under the [MIT Licence](LICENSE).

Third-party source code, model weights and dependencies remain subject to their own licences and attribution requirements.

---

## Final Notice

MarketForge AI helps users inspect data, generate scenarios, compare models and preserve research evidence.

It cannot predict markets with certainty.

Always perform independent research and never risk money that you cannot afford to lose.
