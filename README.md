# MarketForge AI

[![Quality checks](https://github.com/bryanssss/marketforge-ai/actions/workflows/tests.yml/badge.svg)](https://github.com/bryanssss/marketforge-ai/actions/workflows/tests.yml)
[![CodeQL](https://github.com/bryanssss/marketforge-ai/actions/workflows/codeql.yml/badge.svg)](https://github.com/bryanssss/marketforge-ai/actions/workflows/codeql.yml)
[![Licence: MIT](https://img.shields.io/badge/Licence-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Powered-009688.svg)](https://fastapi.tiangolo.com/)
[![Project Status](https://img.shields.io/badge/Status-Research%20Alpha-orange.svg)](#project-status)
[![Local First](https://img.shields.io/badge/Privacy-Local--First-6366f1.svg)](#security-and-privacy)

[![Support MarketForge AI](https://img.shields.io/badge/Support%20MarketForge%20AI-Donate%20with%20PayPal-0070ba?style=for-the-badge&logo=paypal&logoColor=white)](https://www.paypal.com/donate/?hosted_button_id=YE9H5NCNLWU38)

**MarketForge AI** is a local-first financial forecasting, market-data validation, uncertainty analysis and walk-forward backtesting studio.

It provides a polished browser-based interface for importing OHLCV market data, generating probabilistic forecasts, comparing forecasting models, evaluating historical performance and running reproducible financial research workflows.

MarketForge works without Node.js or npm. Its transparent forecasting models run locally, while optional integration with the open-source Kronos financial foundation models can be installed separately.

> **Research and educational software only.**  
> MarketForge AI does not provide financial advice, guaranteed predictions, automated trading signals or promises of profit. Financial markets are uncertain, and historical results do not guarantee future performance.

---

## Table of Contents

- [Overview](#overview)
- [Why MarketForge AI Exists](#why-marketforge-ai-exists)
- [Key Features](#key-features)
- [Forecasting Models](#forecasting-models)
- [Data Validation and Quality Analysis](#data-validation-and-quality-analysis)
- [Walk-Forward Backtesting](#walk-forward-backtesting)
- [Model Comparison](#model-comparison)
- [Prospective Frozen Benchmark v2](#prospective-frozen-benchmark-v2)
- [Quick Start](#quick-start)
- [Install Optional Kronos Support](#install-optional-kronos-support)
- [CSV Data Format](#csv-data-format)
- [Docker](#docker)
- [API](#api)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Security and Privacy](#security-and-privacy)
- [Research Limitations](#research-limitations)
- [Project Status](#project-status)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Third-Party Components](#third-party-components)
- [Licence](#licence)
- [Acknowledgements](#acknowledgements)

---

# Overview

MarketForge AI turns financial forecasting research into a broader, more transparent and user-friendly workflow.

The application allows researchers, developers, students and market-data enthusiasts to:

1. Import historical candlestick data.
2. Validate the quality and structure of the dataset.
3. Detect malformed prices, timestamps and volume values.
4. Generate multiple possible future market paths.
5. View median forecasts and uncertainty intervals.
6. Compare transparent baseline models.
7. Optionally run Kronos Mini, Small or Base.
8. Perform chronological walk-forward backtests.
9. Include fees, slippage, execution delay and risk rules.
10. Measure forecasting accuracy separately from trading performance.
11. Export structured results for further research.
12. Run a preregistered prospective benchmark against a pinned Kronos model.

MarketForge is designed around one important principle:

> A financial forecast should be reproducible, measurable and presented with uncertainty—not displayed as a guaranteed future price.

---

# Why MarketForge AI Exists

The original [Kronos project](https://github.com/shiyu-coder/Kronos) introduced an open-source foundation model designed for financial candlestick data.

Kronos provides an important research foundation, but responsibly evaluating a forecasting model requires more than running inference against a single CSV file.

A complete research workflow also needs:

- Reliable market-data validation
- Clear uncertainty visualisation
- Transparent baseline models
- Chronological evaluation
- Realistic transaction-cost assumptions
- Reproducible model revisions
- Statistical confidence testing
- Security controls
- Automated tests
- Clear research limitations
- Independent comparison against simple methods

MarketForge AI builds these broader product and research layers around optional Kronos integration.

It is not a reskinned copy of the Kronos interface. MarketForge provides its own:

- Browser application
- FastAPI backend
- CSV ingestion pipeline
- Candle-validation system
- Dataset-quality scoring
- Statistical forecasting engines
- Forecast calibration measurements
- Walk-forward backtesting system
- Model-comparison framework
- Prospective benchmark infrastructure
- Security controls
- Docker configuration
- Documentation
- Automated test suite

The Kronos source code and model weights are not bundled with MarketForge.

They remain separate third-party components and are downloaded only when optional Kronos support is installed.

See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) for attribution and licensing information.

---

# Key Features

## Local-First Browser Application

MarketForge runs on your own computer and opens in a normal web browser.

The standard local workflow does not require:

- Node.js
- npm
- A cloud account
- User registration
- A hosted database
- Uploading market data to a MarketForge server
- Downloading large AI weights

Your CSV files and generated results are processed by the local Python application.

## Forecast Studio

The Forecast Studio includes:

- Interactive candlestick charts
- Configurable forecast horizons
- Reproducible random seeds
- Median forecast paths
- Central uncertainty intervals
- Multiple generated scenarios
- Model selection
- Forecast metadata
- JSON result export
- Data-quality summaries

Instead of presenting one future price path as certain, MarketForge generates a distribution of possible outcomes.

## Transparent Baseline Models

MarketForge includes forecasting models that work immediately:

- Naive persistence
- Robust drift
- Moving-block bootstrap
- Ensemble forecast

These models provide understandable reference points against which more complicated models can be evaluated.

## Optional Kronos Integration

MarketForge can optionally connect to:

- Kronos Mini
- Kronos Small
- Kronos Base

The application does not assume that Kronos is automatically better.

Kronos results can be evaluated against the built-in transparent models using matched historical forecast origins.

## Data Quality Scoring

Every imported dataset is inspected for problems such as:

- Missing values
- Invalid prices
- Duplicate timestamps
- Out-of-order timestamps
- Impossible candle relationships
- Negative volume
- Negative amount or turnover
- Irregular time intervals
- Missing candles
- Large return outliers
- Unsupported columns
- Oversized uploads

MarketForge produces a dataset-quality report before forecasting begins.

## Chronological Walk-Forward Evaluation

Historical testing is performed in chronological order.

Each forecast sees only the candles that would have been available at the simulated decision time.

This helps reduce accidental future-data leakage caused by randomly mixing past and future rows.

## Trading-Cost Modelling

Backtests can include:

- Entry fees
- Exit fees
- Slippage
- Execution delay
- Position size
- Forecast thresholds
- Stop-loss rules
- Take-profit rules
- Long-only mode
- Short-only mode
- Long and short mode
- Non-overlapping positions

## Forecast Evidence and Trading Evidence

MarketForge separates forecast quality from strategy profitability.

Forecast measurements include:

- Mean absolute error
- Root mean square error
- Directional accuracy
- Forecast-interval coverage
- Average interval width
- Calibration statistics
- Number of forecast evaluations

Trading measurements include:

- Total return
- Benchmark return
- Excess return
- Win rate
- Maximum drawdown
- Profit factor
- Expectancy
- Average win
- Average loss
- Payoff ratio
- Market exposure
- Long and short trade counts
- Exit-reason statistics

A forecast can be statistically useful without creating a profitable strategy.

A profitable historical simulation also does not prove that a forecasting model is reliable.

---

# Forecasting Models

## Naive Persistence

The naive model assumes that the latest observed market level remains the strongest immediate reference for the next period.

It is intentionally simple and serves as a minimum benchmark.

A more complicated model should not be preferred merely because it is more advanced. It should demonstrate measurable improvement over this baseline.

## Robust Drift

The robust-drift model estimates recent directional movement while reducing the influence of extreme observations.

It is designed to capture short-term movement without relying too heavily on one unusual candle.

## Moving-Block Bootstrap

The moving-block bootstrap samples short, consecutive historical candle patterns.

Unlike independent random-return sampling, this approach can preserve local relationships between:

- Opening gaps
- Candle bodies
- Upper wicks
- Lower wicks
- Volume
- Amount or turnover

The model generates multiple possible future paths and converts them into forecast quantiles.

## Ensemble

The ensemble combines information from multiple transparent forecasting methods.

Its purpose is not to guarantee superior performance.

It provides a candidate model that can be compared against individual baselines and optional Kronos forecasts.

## Kronos Models

When optional Kronos support is installed, MarketForge can use the official Kronos tokenizer and forecasting models.

For uncertainty analysis, MarketForge preserves independent Kronos draws rather than treating one averaged forecast as a complete probability interval.

Kronos forecasting remains subject to:

- Model limitations
- Training-data uncertainty
- Hardware requirements
- Revision-specific behaviour
- Potential domain shift
- Financial-market unpredictability
- Forecast degradation across longer horizons

---

# Data Validation and Quality Analysis

MarketForge expects standard OHLC candlestick data.

## Required Columns

```text
open, high, low, close
```

## Optional Columns

```text
timestamp, volume, amount
```

The application recognises common aliases, including:

```text
date
datetime
time
timestamps
o
h
l
c
vol
turnover
```

## Candle Validation Rules

Each candle must satisfy:

```text
high >= open
high >= close
low <= open
low <= close
high >= low
open > 0
high > 0
low > 0
close > 0
volume >= 0
amount >= 0
```

For normal application use, MarketForge can repair certain malformed values and reports what changed.

Examples include:

- Raising `high` when it is below `open` or `close`
- Lowering `low` when it is above `open` or `close`
- Replacing negative volume with a valid non-negative value
- Removing duplicate timestamps
- Sorting rows chronologically
- Discarding unusable observations
- Estimating missing amount values when possible

The prospective frozen benchmark uses stricter rules and rejects malformed source data instead of silently repairing it.

## Timestamp Analysis

When timestamps are available, MarketForge can:

- Convert values to UTC
- Sort observations chronologically
- Remove duplicated timestamps
- Estimate the expected candle interval
- Detect irregular gaps
- Estimate missing candle counts
- Identify discontinuities in the time series

## Outlier Detection

MarketForge uses robust return-based analysis to identify unusually large movements.

Outlier warnings do not automatically mean that a candle is incorrect.

Large movements can be genuine market events, so users should verify suspicious observations against the original data source.

## Dataset Fingerprints

MarketForge creates a reproducible fingerprint for processed datasets.

This helps researchers confirm that two reports were produced from the same canonical data.

---

# Walk-Forward Backtesting

MarketForge uses rolling historical evaluation rather than random train/test mixing.

A typical simulated decision follows this order:

1. Complete the current historical candle.
2. Build a model context using only past information.
3. Generate a forecast.
4. Apply the configured signal threshold.
5. Wait for the configured execution delay.
6. Enter at a later candle’s opening price.
7. Apply slippage and transaction costs.
8. Process stop-loss and take-profit conditions.
9. Exit at the selected future candle or an earlier risk event.
10. Record both forecast error and trade outcome.

## Next-Candle Execution

MarketForge avoids entering a simulated position at a price already used to create the signal.

Signals are generated from completed historical information, and execution occurs at a later candle according to the configured delay.

## Non-Overlapping Positions

Non-overlapping positions are used by default.

This prevents the simulation from repeatedly applying the same capital to many simultaneous trades unless overlapping exposure is intentionally enabled.

## Conservative Intrabar Handling

When one candle touches both a stop-loss and a take-profit price and the exact intrabar order is unknown, MarketForge uses conservative handling rather than automatically selecting the profitable result.

## Backtest Metrics

Backtest reports can include:

- Number of trades
- Long trades
- Short trades
- Winning trades
- Losing trades
- Win rate
- Total return
- Buy-and-hold return
- Excess return
- Maximum drawdown
- Profit factor
- Average return
- Average win
- Average loss
- Payoff ratio
- Market exposure
- Exit-reason counts

## Backtest Warning

A historical backtest is a simulation.

It may not fully represent:

- Real liquidity
- Bid–ask spreads
- Partial fills
- Exchange outages
- Network latency
- Market impact
- Funding payments
- Borrowing costs
- Tax consequences
- Delisted assets
- Changing market regimes

Backtest results should not be interpreted as expected future returns.

---

# Model Comparison

MarketForge provides matched model comparison.

Models are evaluated using:

- The same dataset
- The same historical dates
- The same lookback period
- The same forecast horizon
- The same forecast origins
- Repeated stochastic seeds where applicable

The comparison system considers:

1. Forecast error
2. Directional accuracy
3. Forecast-interval calibration
4. Stability across seeds
5. Performance relative to the naive baseline

This makes it harder for one unusually successful random run to determine which model appears strongest.

The naive model remains available as the minimum benchmark.

A more complex model should not be considered better unless it demonstrates measurable improvement under matched conditions.

---

# Prospective Frozen Benchmark v2

MarketForge AI 0.4 includes a preregistered prospective benchmark designed to answer one narrow research question:

> Does the frozen MarketForge ensemble produce lower terminal log-return error than the pinned Kronos Base comparator on future, matched market candles?

## Current Status

```text
PREREGISTERED — INCOMPLETE BY DESIGN
```

The benchmark contains no final score and currently makes no superiority claim.

## Frozen Holdout Period

```text
Start:       1 August 2026
End:         31 October 2026
Collection:  3 November 2026 or later
```

Collection is deliberately blocked until after the final official monthly market-data archives should be available.

## Registered Assets

The benchmark covers one-hour candles for:

- BTC/USDT
- ETH/USDT
- BNB/USDT
- SOL/USDT
- XRP/USDT

## Registered Forecast Horizons

```text
1 hour
6 hours
24 hours
```

## Registered Context

The benchmark uses:

```text
400 historical candles
One forecast origin per day
00:00 UTC origins
Matched candidate and comparator dates
```

## Why v2 Replaced v1

The earlier v1 protocol allowed automatic hardware selection.

That could cause different researchers to run inference using CPU, NVIDIA CUDA or Apple MPS, potentially introducing small numerical differences.

V2 was registered before the future holdout began and freezes:

- CPU-only execution
- Deterministic PyTorch algorithms
- One numerical thread
- Python 3.11
- Exact benchmark dependencies
- Exact daily forecast origins
- Exact Kronos source revision
- Exact model revision
- Exact tokenizer revision
- Official archive checksums
- Canonical dataset hashes
- Environment fingerprints
- Prediction-ledger bindings
- Full deterministic replay

The original v1 files remain in the repository as an audit record but are marked as superseded.

## Frozen Model and Source Revisions

The benchmark binds:

- The Kronos Git source revision
- The MarketForge benchmark source fingerprint
- The Kronos model repository revision
- The Kronos tokenizer revision
- Model weight hashes
- Tokenizer weight hashes
- Compatibility-patch hashes
- Benchmark dependency versions
- Benchmark specification hash
- Preregistration hash

If a bound file or revision changes, the original benchmark verification fails.

A changed methodology must use a new benchmark identifier instead of silently replacing v2.

## Dataset Verification

The frozen benchmark checks:

- Official provider ZIP hashes
- Official checksum files
- Local archive hashes
- Canonical CSV hashes
- Expected symbols
- Expected months
- Duplicate timestamps
- Missing candles
- Invalid OHLC values
- Exact forecast origins
- Actual future prices used for scoring

Malformed or incomplete benchmark data is rejected rather than repaired.

## Prediction Ledger

Every frozen prediction is connected to the previous prediction through a cryptographic hash chain.

The ledger records information such as:

- Dataset identity
- Model identity
- Model revision
- Tokenizer revision
- Forecast origin
- Forecast horizon
- Random seed
- Context close
- Forecast median
- Forecast intervals
- Actual future close
- Forecast error
- Previous-record hash
- Current-record hash

## Deterministic Replay

A hash chain can reveal accidental changes, but a complete result set could theoretically be altered and rehashed.

MarketForge therefore performs a full deterministic replay before a final superiority claim is permitted.

The benchmark:

1. Runs every registered prediction.
2. Stores the complete prediction ledger.
3. Runs every prediction again.
4. Compares both ledgers field by field.
5. Refuses the final claim when deterministic values differ.

Runtime duration is excluded because it naturally varies between runs.

Forecasts, prices, intervals, seeds, revisions and dataset identities must match.

## Statistical Tests

The final benchmark report includes:

- Paired absolute terminal log-return errors
- Root mean square error
- Directional accuracy
- Central 80% interval coverage
- Interval score
- Diebold–Mariano tests
- Bartlett-weighted HAC variance
- Moving-block bootstrap confidence intervals
- Holm multiple-comparison correction
- Hierarchical bootstrap confidence intervals

Generated forecast paths are not counted as separate market observations.

For example, eight generated Kronos paths for one timestamp still count as one matched market event.

## Superiority Claim Gate

MarketForge may report that it beat Kronos on this benchmark only if every registered condition passes.

Requirements include:

- All registered tasks completed
- Minimum matched forecast origins per task
- Identical MarketForge and Kronos evaluation dates
- All registered seeds completed
- Global confidence interval entirely below zero
- Minimum proportion of tasks won
- Multiple statistically significant task-level wins
- Holm-adjusted significance requirements
- Minimum mean relative error improvement
- Acceptable uncertainty calibration
- Statistically supported improvement over the naive model
- Successful deterministic replay
- Verified data hashes
- Verified model hashes
- Verified source hashes
- Verified environment hashes
- Verified protocol hashes

Possible final states are:

```text
INCOMPLETE
FAIL
PASS
```

There is no partial, selective or marketing-adjusted result.

## Prepare the Benchmark Environment

### Windows

```text
scripts\setup_benchmark_env_windows.bat
```

### macOS or Linux

```bash
chmod +x scripts/setup_benchmark_env_mac_linux.sh
./scripts/setup_benchmark_env_mac_linux.sh
```

After 3 November 2026, run the matching frozen benchmark script.

### Windows

```text
scripts\run_frozen_benchmark_windows.bat
```

### macOS or Linux

```bash
./scripts/run_frozen_benchmark_mac_linux.sh
```

The final report will be written to:

```text
benchmarks/frozen_v2/results/benchmark_report.md
```

Read [`docs/FROZEN_BENCHMARK.md`](docs/FROZEN_BENCHMARK.md) before running the benchmark or publishing any comparative claim.

---

# Quick Start

## Windows

### Requirements

- Windows 10 or newer
- Python 3.10 or newer
- Internet connection during initial dependency installation

During Python installation, enable:

```text
Add Python to PATH
```

### Start MarketForge

Double-click:

```text
start_windows.bat
```

The script will:

1. Create a local Python virtual environment.
2. Install the required packages.
3. Start the FastAPI server.
4. Open MarketForge in your browser.

The application is available at:

```text
http://127.0.0.1:7070
```

## macOS or Linux

```bash
chmod +x start_mac_linux.sh
./start_mac_linux.sh
```

Then open:

```text
http://127.0.0.1:7070
```

## Manual Installation

Clone the repository:

```bash
git clone https://github.com/bryanssss/marketforge-ai.git
cd marketforge-ai
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the environment.

### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

### Windows Command Prompt

```bat
.venv\Scripts\activate.bat
```

### macOS or Linux

```bash
source .venv/bin/activate
```

Install the application:

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

# Install Optional Kronos Support

Kronos support is optional because its machine-learning dependencies and model weights are significantly larger than the standard MarketForge installation.

## Windows

Run:

```text
scripts\install_kronos_windows.bat
```

## macOS or Linux

```bash
chmod +x scripts/install_kronos_mac_linux.sh
./scripts/install_kronos_mac_linux.sh
```

The installer:

1. Downloads the official Kronos repository.
2. Checks out a pinned source revision.
3. Places it under `vendor/Kronos`.
4. Installs the required machine-learning dependencies.
5. Applies the documented compatibility patch when required.
6. Records source and patch hashes.
7. Enables Kronos model selection inside MarketForge.

Model weights are downloaded separately from Hugging Face when first requested.

The weights are not stored in this Git repository.

## Kronos Hardware Considerations

Kronos inference may be slow on ordinary computers.

Kronos Mini is generally the smallest available option.

Kronos Small and Base may require:

- More system memory
- Longer inference times
- A supported GPU for practical performance
- Additional disk space for downloaded weights

The standard MarketForge baseline models remain available when Kronos is not installed.

---

# CSV Data Format

A simple compatible CSV looks like this:

```csv
timestamp,open,high,low,close,volume
2026-01-01T00:00:00Z,42000,42450,41800,42250,1250.4
2026-01-01T01:00:00Z,42250,42600,42100,42520,1184.7
2026-01-01T02:00:00Z,42520,42780,42330,42410,1092.1
```

## Recommendations

For the most reliable results:

- Use one consistent timeframe.
- Use UTC timestamps.
- Sort rows from oldest to newest.
- Avoid mixing different assets in one file.
- Include at least several hundred candles.
- Avoid manually rounded prices when precise values are available.
- Preserve the original source file separately.
- Inspect the MarketForge quality report before forecasting.
- Confirm that the file does not contain future information unavailable at the evaluation date.

---

# Docker

Build and start the application with:

```bash
docker compose up --build
```

Open:

```text
http://localhost:7070
```

The supplied container configuration includes:

- A non-root application user
- A health check
- Dropped Linux capabilities
- Read-only filesystem settings
- Local port binding by default
- Resource-conscious application defaults

Real Kronos inference may require significantly more memory than the transparent baseline models.

---

# API

Interactive FastAPI documentation is available at:

```text
http://127.0.0.1:7070/docs
```

Alternative ReDoc documentation is available at:

```text
http://127.0.0.1:7070/redoc
```

## Main Endpoints

### Health

```http
GET /api/health
```

Returns application status, version information and optional Kronos availability.

### Sample Dataset

```http
GET /api/sample
```

Downloads a sample OHLCV CSV file.

### Analyse Data

```http
POST /api/analyse
```

Validates an uploaded dataset and returns quality information.

### Generate Forecast

```http
POST /api/forecast
```

Generates a forecast using the selected model and configuration.

### Run Backtest

```http
POST /api/backtest
```

Runs a chronological walk-forward strategy simulation.

### Compare Models

```http
POST /api/compare
```

Evaluates multiple models using matched historical forecast origins.

## Heavy-Job Limits

Forecasting, comparison and backtesting can be computationally expensive.

The server limits concurrent heavy jobs using:

```text
MARKETFORGE_MAX_CONCURRENT_JOBS
```

The default is designed to reduce the chance of exhausting the host computer.

---

# Testing

Install development test tools:

```bash
pip install pytest pytest-cov
```

Run the complete test suite:

```bash
pytest -q
```

Run with coverage:

```bash
pytest -q --cov=app --cov-report=term-missing
```

Compile-check the Python source:

```bash
python -m compileall app scripts tests run.py
```

## Automated GitHub Checks

GitHub Actions performs:

- Python tests
- Coverage validation
- Python compatibility checks
- Production-critical Ruff checks
- Browser JavaScript validation
- Frozen benchmark smoke checks
- Dependency auditing
- CodeQL security analysis

The repository tests application behaviour across multiple supported Python versions.

---

# Project Structure

```text
marketforge-ai/
├── .github/
│   ├── workflows/             # Tests, security and benchmark checks
│   └── dependabot.yml
├── app/
│   ├── api/                   # FastAPI endpoints
│   ├── benchmark/             # Frozen benchmark engine
│   ├── core/                  # Configuration and shared utilities
│   ├── forecasting/           # Forecast models and adapters
│   ├── services/              # Data, forecast and backtest services
│   ├── static/                # Browser interface assets
│   └── templates/             # HTML templates
├── benchmarks/
│   ├── frozen_v1/             # Superseded audit record
│   └── frozen_v2/             # Official prospective benchmark
├── data/                      # Sample or local data area
├── docs/                      # Technical and beginner documentation
├── scripts/                   # Installation and benchmark scripts
├── tests/                     # Automated test suite
├── vendor/                    # Optional third-party checkout location
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-kronos.txt
├── requirements-benchmark.txt
├── run.py
├── start_windows.bat
├── start_mac_linux.sh
├── SECURITY.md
├── CONTRIBUTING.md
├── THIRD_PARTY_NOTICES.md
└── LICENSE
```

---

# Security and Privacy

MarketForge is designed for local research workflows.

The application includes controls such as:

- Request-size limits
- Upload-size limits
- Dataset row and column limits
- Trusted-host validation
- Sanitised server errors
- Request identifiers
- Content Security Policy
- Clickjacking protection
- MIME-sniffing protection
- Restricted browser permissions
- No-store API responses
- Heavy-job concurrency limits
- Non-root Docker execution
- Dependency auditing
- CodeQL scanning

## Never Commit Sensitive Information

Do not add the following to Git:

- Exchange API keys
- Passwords
- Private account statements
- Personal trading histories
- `.env` files
- Cryptocurrency wallet secrets
- Downloaded model weights
- Local virtual environments
- Confidential datasets
- Authentication cookies
- Private research data

The included `.gitignore` blocks many common sensitive or unnecessary files, but users should still inspect every commit before publishing it.

Security issues should be reported according to [`SECURITY.md`](SECURITY.md).

---

# Research Limitations

MarketForge provides tools for research, not certainty.

Important limitations include:

- Financial markets are non-stationary.
- Forecast relationships can disappear.
- Model performance may vary across assets and timeframes.
- Historical data may contain errors.
- Public models may have uncertain training-data boundaries.
- Simulated execution differs from real execution.
- Forecast intervals may be miscalibrated.
- Statistical significance does not guarantee profitability.
- A successful benchmark does not prove universal superiority.
- Model outputs can appear plausible while still being incorrect.
- Transaction costs can remove apparent historical advantages.
- Market regimes can change without warning.
- Historical liquidity may not represent live liquidity.
- Model performance can degrade after publication.

Users should independently verify:

- Dataset provenance
- Timestamp consistency
- Model revision
- Evaluation period
- Transaction-cost assumptions
- Risk calculations
- Statistical methodology
- Benchmark independence
- Whether any future information entered the analysis

---

# Project Status

MarketForge AI is currently an **alpha research release**.

The following areas are functional:

- Browser interface
- Local FastAPI server
- CSV ingestion
- Candle validation
- Dataset-quality reporting
- Transparent forecasting models
- Forecast uncertainty ranges
- Walk-forward backtesting
- Model comparison
- JSON export
- Optional Kronos adapter
- Docker packaging
- Automated tests
- CodeQL analysis
- Prospective frozen benchmark infrastructure

The prospective benchmark is preregistered but has not yet reached its future evaluation period.

No claim is currently made that MarketForge produces more accurate forecasts than Kronos.

---

# Roadmap

Potential future improvements include:

- Additional market-data connectors
- Direct exchange-data import
- Additional forecasting models
- Portfolio-level simulations
- Position-allocation tools
- Improved chart controls
- Saved research projects
- Experiment tracking
- Model registry support
- More report templates
- Additional calibration methods
- Expanded performance diagnostics
- Desktop packaging
- Better accessibility
- Additional interface languages
- Multi-asset analysis
- Market-regime classification
- Volatility forecasting
- Scenario stress testing
- Independent external benchmark replication

See [`ROADMAP.md`](ROADMAP.md) for development priorities.

---

# Contributing

Contributions are welcome.

Suitable contributions include:

- Bug fixes
- Automated tests
- Documentation improvements
- Accessibility improvements
- Additional transparent baselines
- Data-validation improvements
- Security hardening
- Performance improvements
- Reproducibility tools
- Benchmark verification tools

Before making a large change, open an issue explaining:

- The problem
- The proposed solution
- Possible research implications
- Possible security implications
- Whether frozen benchmark files would be affected

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) before submitting a pull request.

## Frozen Benchmark Changes

Do not silently modify the official v2 benchmark methodology.

Changes to benchmark-bound logic must use a new benchmark identifier rather than replacing the preregistered protocol.

The following areas should be treated as frozen for benchmark v2:

```text
benchmarks/frozen_v2/spec.json
benchmarks/frozen_v2/model_lock.json
benchmarks/frozen_v2/preregistration_lock.json
app/benchmark/
scripts/benchmark.py
requirements-benchmark.txt
```

---

# Third-Party Components

MarketForge AI includes optional support for the Kronos financial foundation model.

Kronos was created by its respective authors and remains a separate third-party open-source project.

MarketForge does not claim ownership of:

- The Kronos architecture
- The Kronos tokenizer
- Kronos pretrained weights
- Original Kronos research
- Third-party datasets used by Kronos

The Kronos repository and publicly released components are subject to their own licences and attribution requirements.

See:

- [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)
- [Official Kronos repository](https://github.com/shiyu-coder/Kronos)

---

# Licence

MarketForge AI is released under the [MIT Licence](LICENSE).

You may use, copy, modify, distribute and commercially use the original MarketForge portions of this repository, subject to the terms of the MIT Licence.

Third-party software, model weights and downloaded dependencies remain subject to their own licences.

Preserve all required copyright and attribution notices when redistributing third-party components.

---

# Acknowledgements

MarketForge AI acknowledges the researchers and developers behind:

- The Kronos financial foundation model
- PyTorch
- FastAPI
- pandas
- NumPy
- Hugging Face
- Plotly and browser-charting tools
- Pytest
- Ruff
- The wider open-source Python ecosystem

Their work makes independent financial machine-learning research more accessible.

---

# Repository

```text
https://github.com/bryanssss/marketforge-ai
```

---

# Final Notice

MarketForge AI helps users inspect market data, generate scenarios, compare models and evaluate forecasting methods.

It cannot predict markets with certainty.

Always perform independent research and never risk money that you cannot afford to lose.
