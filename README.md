# MarketForge AI

[![Quality checks](https://github.com/bryanssss/marketforge-ai/actions/workflows/tests.yml/badge.svg)](https://github.com/bryanssss/marketforge-ai/actions/workflows/tests.yml)
[![CodeQL](https://github.com/bryanssss/marketforge-ai/actions/workflows/codeql.yml/badge.svg)](https://github.com/bryanssss/marketforge-ai/actions/workflows/codeql.yml)
[![Dependency audit](https://github.com/bryanssss/marketforge-ai/actions/workflows/security.yml/badge.svg)](https://github.com/bryanssss/marketforge-ai/actions/workflows/security.yml)
[![Licence: MIT](https://img.shields.io/badge/Licence-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Powered-009688.svg)](https://fastapi.tiangolo.com/)
[![Release](https://img.shields.io/badge/Release-v0.5.0-2563eb.svg)](https://github.com/bryanssss/marketforge-ai/releases/tag/v0.5.0)
[![Status](https://img.shields.io/badge/Status-Research%20Alpha-orange.svg)](#project-status)
[![Privacy](https://img.shields.io/badge/Privacy-Local--First-6366f1.svg)](#privacy-and-security)

[![Support MarketForge AI](https://img.shields.io/badge/Support%20MarketForge%20AI-Donate%20with%20PayPal-0070ba?style=for-the-badge&logo=paypal&logoColor=white)](https://www.paypal.com/donate/?hosted_button_id=YE9H5NCNLWU38)

**MarketForge AI** is a local-first AI market forecasting, financial data validation, portfolio analysis, volatility research and walk-forward backtesting workbench.

Import OHLCV candlestick data from CSV files or supported public exchange endpoints, generate probabilistic forecasts, compare transparent forecasting models, classify market regimes, simulate portfolios, forecast volatility, run stress scenarios, track experiments and preserve reproducible research evidence—all through a polished browser interface.

The standard application requires Python but does **not** require Node.js, npm, registration, a cloud account or a hosted application server.

Optional Kronos support and optional desktop packaging can be installed separately.

> **Research and educational software only.**  
> MarketForge AI does not provide financial advice, guaranteed predictions, automated trading signals or promises of profit. Financial markets are uncertain, and historical performance does not guarantee future results.

---

## Table of Contents

- [Overview](#overview)
- [What Is New in Version 0.5](#what-is-new-in-version-05)
- [Why MarketForge AI Exists](#why-marketforge-ai-exists)
- [Core Features](#core-features)
- [Forecasting Models](#forecasting-models)
- [Forecast Calibration](#forecast-calibration)
- [Direct Exchange Data Imports](#direct-exchange-data-imports)
- [Data Validation and Quality Analysis](#data-validation-and-quality-analysis)
- [Walk-Forward Backtesting](#walk-forward-backtesting)
- [Portfolio and Multi-Asset Research](#portfolio-and-multi-asset-research)
- [Research Lab](#research-lab)
- [Projects and Experiment Tracking](#projects-and-experiment-tracking)
- [Local Model Registry](#local-model-registry)
- [Research Reports](#research-reports)
- [External Benchmark Replication](#external-benchmark-replication)
- [Prospective Frozen Benchmark v3](#prospective-frozen-benchmark-v3)
- [Quick Start](#quick-start)
- [Optional Kronos Support](#optional-kronos-support)
- [Desktop Packaging](#desktop-packaging)
- [CSV Data Format](#csv-data-format)
- [Docker](#docker)
- [API](#api)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Privacy and Security](#privacy-and-security)
- [Research Limitations](#research-limitations)
- [Project Status](#project-status)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Support This Free Project](#support-this-free-project)
- [Third-Party Components](#third-party-components)
- [Licence](#licence)
- [Acknowledgements](#acknowledgements)
- [Final Notice](#final-notice)

---

# Overview

MarketForge AI turns financial forecasting research into a broader, transparent and reproducible research workflow.

It allows researchers, developers, students and market-data enthusiasts to:

1. Import historical candlestick data.
2. Download recent public market data from supported exchanges.
3. Validate the quality and structure of each dataset.
4. Detect malformed prices, timestamps and volume values.
5. Generate multiple possible future market paths.
6. View median forecasts and uncertainty intervals.
7. Compare transparent forecasting models.
8. Optionally run Kronos Mini, Small or Base.
9. Classify current market regimes.
10. Estimate future volatility.
11. Run chronological walk-forward simulations.
12. Include fees, slippage, execution delays and risk rules.
13. Analyse multiple assets and portfolio allocations.
14. Run configurable market stress scenarios.
15. Save projects and research experiments locally.
16. Generate structured Markdown and HTML reports.
17. Analyse external benchmark-replication ledgers.
18. Run a preregistered prospective benchmark against a pinned Kronos model.

MarketForge is designed around one important principle:

> A financial forecast should be reproducible, measurable and presented with uncertainty—not displayed as a guaranteed future price.

---

# What Is New in Version 0.5

Version 0.5 transforms MarketForge from a forecasting and backtesting application into a broader local-first financial research workbench.

## Public Market-Data Connectors

MarketForge can now import public historical candles from:

- Binance Spot
- Coinbase Exchange
- Kraken Spot

The connectors are read-only and do not require private exchange API keys.

## Additional Forecasting Models

Version 0.5 adds:

- Exponential smoothing
- Momentum forecasting
- Mean-reversion forecasting
- Regime-aware ensemble forecasting

These join the existing naive, robust-drift, moving-block-bootstrap and general ensemble models.

## Forecast Calibration

Forecast uncertainty intervals can now use:

- No calibration
- Empirical calibration
- Widen-only conformal-style calibration

Calibration information is stored in forecast metadata.

## Portfolio Research

The new Portfolio workspace supports:

- Multi-asset alignment
- Correlation analysis
- Covariance analysis
- Equal-weight allocation
- Inverse-volatility allocation
- Risk-parity allocation
- Minimum-variance allocation
- Weight constraints
- Rebalancing
- Turnover
- Transaction costs
- Portfolio equity analysis
- Maximum drawdown analysis

## Research Lab

The new Research Lab includes:

- Market-regime classification
- EWMA volatility forecasting
- Parkinson volatility estimation
- Garman–Klass volatility estimation
- Volatility ensemble estimates
- Scenario stress testing
- Value at risk
- Expected shortfall
- Loss-probability analysis

## Saved Research Workspace

MarketForge now includes local SQLite storage for:

- Saved projects
- Research settings
- Dataset fingerprints
- Experiment history
- Result metrics
- Result hashes
- Tags
- Local model metadata

## Reports and Replication

Version 0.5 adds:

- Executive reports
- Full research reports
- Risk reports
- Model cards
- Markdown export
- HTML export
- External benchmark-replication analysis

## Accessibility and Languages

The interface now includes foundations for:

- English
- Bulgarian
- Spanish
- High-contrast mode
- Reduced-motion mode
- Improved keyboard focus
- Accessible chart-data tables
- Better screen-reader guidance

## Desktop Packaging

Optional PyWebView and PyInstaller tools are included for building standalone desktop packages.

## Prospective Benchmark v3

A new prospective benchmark was created because the candidate forecasting engine changed after benchmark v2 was publicly registered.

Benchmark v2 remains preserved as an audit record. Version 0.5 uses prospective frozen benchmark v3.

See [`CHANGELOG.md`](CHANGELOG.md) for the complete version history.

---

# Why MarketForge AI Exists

The original [Kronos project](https://github.com/shiyu-coder/Kronos) introduced an open-source foundation model for financial candlestick data.

Kronos provides an important research foundation, but a forecasting model alone is not a complete research workflow.

Responsible financial forecasting research also needs:

- Reliable market-data validation
- Transparent reference models
- Clear uncertainty intervals
- Chronological evaluation
- Realistic execution timing
- Fees and slippage
- Portfolio-level analysis
- Forecast calibration
- Reproducible model revisions
- Statistical confidence testing
- Security controls
- Automated tests
- Clear research limitations
- Independent replication

MarketForge AI builds these broader product and research layers around optional Kronos integration.

MarketForge is not a reskinned copy of the Kronos interface. It provides its own:

- Browser application
- FastAPI backend
- CSV ingestion system
- Public market-data connectors
- Candle-validation pipeline
- Dataset-quality scoring
- Transparent forecasting models
- Forecast calibration tools
- Walk-forward backtesting engine
- Multi-asset portfolio simulator
- Market-regime classifier
- Volatility-forecasting tools
- Stress-testing system
- Research-project storage
- Experiment tracker
- Model registry
- Report generator
- External replication analyser
- Prospective benchmark infrastructure
- Security controls
- Docker packaging
- Desktop packaging foundations
- Documentation
- Automated test suite

The Kronos source code and model weights are not bundled with MarketForge.

They remain separate third-party components and are downloaded only when optional Kronos support is installed.

See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) for attribution and licensing information.

---

# Core Features

## Local-First Browser Studio

MarketForge runs on your computer and opens in a normal web browser.

The normal local workflow does not require:

- Node.js
- npm
- A cloud account
- User registration
- A hosted database
- Uploading data to a MarketForge-operated server
- Downloading large AI model weights

The application is normally available at:

```text
http://127.0.0.1:7070
```

Your uploaded CSV files and generated results are processed by the local Python application.

A separately hosted MarketForge deployment processes information on whichever server the operator configures.

## Forecast Studio

The Forecast Studio provides:

- Interactive candlestick charts
- Configurable forecast lookback
- Configurable forecast horizon
- Reproducible random seeds
- Multiple generated paths
- Median forecast paths
- Central uncertainty intervals
- Optional interval calibration
- Forecast-model selection
- Market-regime information
- Forecast metadata
- JSON result export
- Accessible table representation
- Adjustable visible chart history

Instead of presenting one future price line as certain, MarketForge generates a distribution of possible outcomes.

## Transparent Models

MarketForge includes forecasting models that work immediately without requiring large third-party AI weights.

These models provide understandable reference points against which more complicated systems can be evaluated.

## Optional Kronos Models

MarketForge can optionally connect to:

- Kronos Mini
- Kronos Small
- Kronos Base

Kronos results can be compared against MarketForge’s transparent models using matched historical forecast origins.

## Model Comparison

Models can be evaluated using:

- The same dataset
- The same lookback period
- The same forecast horizon
- The same historical dates
- The same forecast origins
- Repeated stochastic seeds where applicable

The comparison system considers:

- Forecast error
- Directional accuracy
- Forecast-interval calibration
- Stability across seeds
- Performance relative to a naive baseline

A more complex model should not be preferred simply because it sounds more advanced.

---

# Forecasting Models

MarketForge includes eight transparent forecasting choices.

| Model | Description |
|---|---|
| `naive` | Near-persistence reference model |
| `drift` | Robust recent drift with stochastic shocks |
| `block_bootstrap` | Resamples consecutive historical candle patterns |
| `exponential_smoothing` | Emphasises recent returns with decaying weights |
| `momentum` | Extends weighted recent direction with controlled decay |
| `mean_reversion` | Pulls price towards an exponential anchor |
| `ensemble` | General blend of block, drift and naive paths |
| `regime_ensemble` | Selects a transparent mixture based on the detected market regime |

## Naive Persistence

The naive model assumes that the latest observed market level remains the strongest immediate reference for the next period.

It is intentionally simple and acts as a minimum benchmark.

## Robust Drift

The robust-drift model estimates recent directional movement while reducing the influence of extreme observations.

## Moving-Block Bootstrap

The moving-block bootstrap samples short, consecutive historical candle patterns.

Unlike independent random-return sampling, this can preserve local relationships between:

- Opening gaps
- Candle bodies
- Upper wicks
- Lower wicks
- Volume
- Amount or turnover

## Exponential Smoothing

The exponential-smoothing model gives more importance to recent returns while allowing the influence of older observations to decay.

## Momentum

The momentum model estimates weighted recent direction and projects a controlled, decaying version of that movement.

## Mean Reversion

The mean-reversion model estimates an exponential price anchor and simulates movement back towards that reference.

## General Ensemble

The general ensemble combines naive, robust-drift and moving-block-bootstrap information.

## Regime-Aware Ensemble

The regime-aware ensemble changes its transparent model mixture according to recent evidence such as:

- Trend direction
- Trend strength
- Momentum
- Volatility
- Market noise
- Regime confidence

The regime-aware ensemble is the registered MarketForge candidate in prospective frozen benchmark v3.

## Optional Kronos Models

When optional Kronos support is installed, MarketForge can use the official Kronos tokenizer and forecasting models.

For uncertainty analysis, MarketForge preserves independent Kronos draws instead of treating one averaged path as a complete probability interval.

Kronos remains subject to:

- Model limitations
- Training-data uncertainty
- Hardware requirements
- Revision-specific behaviour
- Domain shift
- Forecast degradation
- Financial-market unpredictability

---

# Forecast Calibration

MarketForge can adjust generated forecast intervals using several calibration modes.

## No Calibration

The original model interval is returned without an additional adjustment.

## Empirical Calibration

Recent historical forecast behaviour is used to estimate whether intervals should be widened.

## Widen-Only Conformal-Style Calibration

The conformal-style option can widen intervals based on recent residual evidence.

It does not artificially narrow an interval simply to make the forecast appear more precise.

Calibration details are recorded in forecast metadata so that adjustments remain visible and auditable.

Calibration does not guarantee that future observations will fall inside the reported interval.

---

# Direct Exchange Data Imports

The browser interface can import recent public market candles from:

- Binance Spot
- Coinbase Exchange
- Kraken Spot

## Connector Principles

The connectors:

- Use public market-data endpoints
- Do not request private trading API keys
- Do not access user exchange accounts
- Do not place orders
- Use fixed supported provider hosts
- Pass imported data through the normal MarketForge validation pipeline

Provider limits differ. MarketForge displays provider-specific intervals and maximum recent candle counts.

Imported candles are converted into the normal MarketForge data format and then use the same analysis, forecasting and backtesting workflow as manually uploaded CSV files.

> Public endpoint availability, regional access, symbol naming, historical limits and rate limits remain controlled by each provider.

---

# Data Validation and Quality Analysis

MarketForge expects standard OHLC candlestick data.

## Required Columns

```text
open, high, low, close
```

## Recommended Columns

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

Each candle should satisfy:

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

## Quality Checks

MarketForge checks for:

- Missing required OHLC fields
- Invalid prices
- Non-positive prices
- Impossible candle relationships
- Duplicate timestamps
- Out-of-order rows
- Missing values
- Negative volume
- Negative amount or turnover
- Irregular time intervals
- Estimated missing candles
- Large return outliers
- Unsupported columns
- Oversized uploads
- Binary or malformed uploads

## Normal Application Repairs

Normal application mode can repair selected malformed values and reports every change.

Examples include:

- Raising `high` when it is below `open` or `close`
- Lowering `low` when it is above `open` or `close`
- Removing duplicate timestamps
- Sorting rows chronologically
- Replacing invalid negative volume
- Estimating missing amount when possible
- Discarding unusable observations

## Frozen Benchmark Rules

Frozen benchmark mode does not silently repair invalid benchmark source data.

Malformed, incomplete or checksum-invalid data is rejected.

## Dataset Fingerprints

MarketForge creates reproducible fingerprints for processed datasets.

This helps researchers confirm that different reports were generated from the same canonical data.

---

# Walk-Forward Backtesting

MarketForge performs rolling chronological evaluation instead of randomly mixing historical rows.

A simulated decision follows this general order:

1. Complete the current historical candle.
2. Build a model context using only previously available information.
3. Generate a forecast.
4. Apply the configured signal threshold.
5. Wait for the configured execution delay.
6. Enter at a later candle’s opening price.
7. Apply fees and slippage.
8. Process stop-loss and take-profit conditions.
9. Exit at the selected future candle or an earlier risk event.
10. Record both forecasting evidence and trade evidence.

## Backtest Controls

Controls include:

- Forecast threshold
- Long-only mode
- Short-only mode
- Long and short mode
- Entry fees
- Exit fees
- Slippage
- Position size
- Execution delay
- Stop loss
- Take profit
- Optional overlapping positions

## Next-Candle Execution

MarketForge avoids entering a simulated trade at a price already used to generate the signal.

Signals are created from completed historical information, while execution occurs later according to the selected delay.

## Non-Overlapping Positions

Non-overlapping positions are used by default.

This prevents the same simulated capital from being reused across many simultaneous positions unless overlapping exposure is deliberately enabled.

## Conservative Intrabar Handling

When one candle touches both a stop and a target and the exact intrabar order is unknown, MarketForge uses conservative handling instead of automatically selecting the profitable result.

## Forecast Evidence

Forecast measurements include:

- Mean absolute error
- Root mean square error
- Directional accuracy
- Forecast-interval coverage
- Average interval width
- Calibration statistics
- Number of evaluated forecasts

## Trading Evidence

Trading measurements include:

- Total return
- Buy-and-hold return
- Excess return
- Number of trades
- Long trades
- Short trades
- Win rate
- Maximum drawdown
- Profit factor
- Expectancy
- Average win
- Average loss
- Payoff ratio
- Market exposure
- Exit-reason statistics

A forecast can be statistically useful without producing a profitable strategy.

A profitable historical simulation also does not prove that a forecasting model is reliable.

## Backtest Warning

A historical simulation may not fully represent:

- Real liquidity
- Bid–ask spreads
- Partial fills
- Exchange outages
- Network latency
- Market impact
- Borrowing costs
- Funding payments
- Taxes
- Delisted assets
- Changing market regimes

Backtest results should not be interpreted as expected future returns.

---

# Portfolio and Multi-Asset Research

MarketForge can analyse between two and twenty CSV datasets using their matching timestamps.

## Multi-Asset Diagnostics

The multi-asset workspace can calculate:

- Aligned return history
- Matching date range
- Correlation matrix
- Covariance relationships
- Per-asset return
- Per-asset volatility
- Equal-weight diversification ratio

## Allocation Methods

Supported portfolio-allocation approaches include:

- Equal weight
- Inverse volatility
- Risk parity
- Minimum variance

## Simulation Controls

Portfolio controls include:

- Trailing allocation lookback
- Rebalancing frequency
- Minimum position weight
- Maximum position weight
- Transaction fees
- Initial capital
- Optional target volatility

## Portfolio Results

Results include:

- Final equity
- Total return
- Maximum drawdown
- Per-candle volatility
- Sharpe-style ratio
- Sortino-style ratio
- Total turnover
- Rebalancing history
- Weight history
- Latest allocation

This remains a research simulation and does not model every live execution constraint.

Portfolio covariance estimates can be unstable, especially when based on short or unusual historical periods.

---

# Research Lab

## Market-Regime Classification

The regime tool analyses the current market window and can describe conditions such as:

- Uptrend
- Downtrend
- Sideways market
- High-volatility trend
- Low-volatility sideways market
- Liquidity shock
- Uncertain or transitional regime

The result includes supporting evidence such as:

- Trend direction
- Trend strength
- Recent return
- Realised volatility
- Volatility percentile
- Momentum
- Downside and upside volatility asymmetry
- Regime confidence

## Volatility Forecasting

Available volatility estimators include:

- EWMA close-return variance
- Parkinson high-low estimator
- Garman–Klass OHLC estimator
- Combined ensemble estimate

Results can include:

- Per-candle volatility
- Horizon-adjusted volatility
- Annualised volatility
- Volatility percentile
- Risk-regime description

## Scenario Stress Testing

Stress controls include:

- Immediate price shock
- Volatility multiplier
- Volume or liquidity shock
- Liquidity cost
- Number of simulated scenarios
- Confidence level
- Reproducible random seed

Outputs include:

- Median stressed return
- Expected stressed return
- Best scenario
- Worst scenario
- Loss probability
- Value at risk
- Expected shortfall
- Return-distribution percentiles

Stress scenarios are assumptions, not predictions.

---

# Projects and Experiment Tracking

MarketForge creates a local SQLite research database at:

```text
storage/marketforge.db
```

The storage folder is excluded from Git by default.

## Saved Projects

Projects can record:

- Project name
- Description
- Interface language
- Research settings
- Dataset fingerprints
- Creation timestamp
- Update timestamp

## Experiment Tracking

Saved experiments can include:

- Experiment type
- Dataset fingerprint
- Model settings
- Forecast horizon
- Evaluation metrics
- Result data
- Tags
- SHA-256 result hash
- Creation timestamp

This makes it easier to compare research results without relying only on screenshots, browser history or handwritten notes.

## Storage Warning

The local SQLite database is not designed to store secrets.

Do not store:

- Passwords
- Exchange API keys
- Wallet seed phrases
- Authentication cookies
- Private financial records
- Confidential personal information

Back up `storage/marketforge.db` before replacing or reinstalling the application when you want to preserve saved research.

---

# Local Model Registry

The local model registry stores model identity and metadata.

Registry fields can include:

- Model name
- Model family
- Version
- Source
- Revision
- Checksum
- Additional metadata
- Active status

The registry is metadata-only.

Adding a registry entry does not automatically download or execute arbitrary third-party Python code.

This limitation is intentional and reduces the risk of unsafe model plug-ins.

---

# Research Reports

MarketForge can generate downloadable research reports in:

- Markdown
- HTML

## Report Templates

Available templates include:

- Executive summary
- Full research report
- Risk report
- Model card

Reports can include:

- Main metrics
- Research settings
- Dataset identity
- Model information
- Evidence notes
- Limitations
- Risk warnings
- Additional metadata

Reports preserve research information but do not independently verify that the underlying data, assumptions or model are correct.

---

# External Benchmark Replication

MarketForge includes an analyser for external prediction ledgers.

A compatible ledger contains:

```csv
origin,model,actual,prediction
2026-01-01T00:00:00Z,candidate,101.0,100.7
2026-01-01T00:00:00Z,comparator,101.0,100.2
```

The analyser performs:

- Matched-origin evaluation
- Candidate and comparator alignment
- Terminal log-return forecast errors
- Relative error improvement
- Diebold–Mariano comparison
- Moving-block bootstrap
- Confidence-interval calculation
- Statistical decision reporting

See [`docs/EXTERNAL_REPLICATION.md`](docs/EXTERNAL_REPLICATION.md).

The analyser verifies submitted calculations.

It cannot independently prove that:

- The dataset was genuinely untouched
- The models were frozen before testing
- Training contamination was impossible
- Unsuccessful observations were not removed before submission

Independent replication still depends on transparent research practices.

---

# Prospective Frozen Benchmark v3

MarketForge AI 0.5 introduces **Prospective Frozen Benchmark v3** because the candidate forecasting engine changed after benchmark v2 was publicly preregistered.

Benchmark v1 and benchmark v2 remain preserved as audit records.

The current official MarketForge 0.5 protocol is benchmark v3.

## Registered Research Question

> Does the frozen MarketForge regime-aware ensemble produce lower terminal log-return error than the pinned Kronos Base comparator on future, matched market candles?

## Current Status

```text
PREREGISTERED — INCOMPLETE BY DESIGN
```

The benchmark currently contains no final score and makes no superiority claim.

## Frozen Holdout Period

```text
Start:       1 August 2026
End:         31 October 2026
Collection:  3 November 2026 or later
```

Collection is deliberately blocked until after the final official monthly archives should be available.

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

## Registered Context and Origins

```text
Context:     400 historical candles
Frequency:   One forecast origin per day
Origin time: 00:00 UTC
```

Candidate and comparator models must use identical matched origins.

## Registered Candidate

```text
marketforge-regime-ensemble
```

The candidate uses the frozen regime-aware ensemble with registered empirical interval calibration.

## Registered Comparator

```text
kronos-base
```

The Kronos source, model revision, tokenizer revision and expected hashes are pinned in the benchmark lock files.

## Frozen Execution Environment

Benchmark v3 freezes:

- CPU-only execution
- Deterministic PyTorch algorithms
- One numerical thread
- Python 3.11
- Exact direct benchmark dependencies
- Exact daily forecast origins
- Exact Kronos source revision
- Exact Kronos model revision
- Exact Kronos tokenizer revision
- Registered MarketForge candidate
- Registered empirical calibration
- Central 80% interval
- Official archive checksums
- Canonical dataset hashes
- Environment fingerprints
- Prediction-ledger bindings
- Full deterministic replay
- Statistical superiority requirements

## Dataset Verification

The benchmark checks:

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

Malformed or incomplete benchmark data is rejected instead of repaired.

## Prediction Ledger

Every prediction is connected to the previous prediction through a cryptographic hash chain.

Records include information such as:

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

A hash chain can reveal accidental editing, but a complete ledger could theoretically be replaced and rehashed.

MarketForge therefore performs a full deterministic replay before a superiority claim is allowed.

The benchmark:

1. Runs every registered prediction.
2. Stores the complete prediction ledger.
3. Runs every prediction again.
4. Compares both ledgers field by field.
5. Rejects the claim when deterministic values differ.

Runtime duration is excluded because it naturally varies.

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

For example, several generated paths for one timestamp still count as one matched market event.

## Superiority Claim Gate

MarketForge may report that it beat Kronos on this benchmark only when every registered requirement passes.

Requirements include:

- All registered tasks completed
- Minimum matched origins per task
- Identical candidate and Kronos evaluation dates
- Every registered seed completed
- Global confidence interval entirely below zero
- Minimum proportion of tasks won
- Multiple statistically significant task-level wins
- Holm-adjusted significance requirements
- Minimum mean relative error improvement
- Acceptable interval calibration
- Statistically supported improvement over the naive baseline
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

There is no partial or marketing-adjusted result.

## Benchmark Seal

The official v3 preregistration seal is stored in:

```text
benchmarks/frozen_v3/preregistration_lock.json
```

Check the current benchmark status with:

```bash
python scripts/benchmark.py status
```

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

The final report will be written under:

```text
benchmarks/frozen_v3/results/
```

Read [`docs/FROZEN_BENCHMARK.md`](docs/FROZEN_BENCHMARK.md) before running the benchmark or publishing a comparison claim.

Do not modify benchmark-bound source or lock files under the same benchmark identifier.

A methodological change requires a new benchmark version and a new preregistration.

---

# Quick Start

## Windows

### Requirements

- Windows 10 or newer
- Python 3.10 or newer
- Internet access during the first dependency installation

During Python installation, enable:

```text
Add Python to PATH
```

### Start MarketForge

Extract the repository or release ZIP and double-click:

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

Activate it.

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

Install and start the application:

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

# Optional Kronos Support

Kronos support is optional because its machine-learning dependencies and model weights are substantially larger than the standard MarketForge installation.

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
6. Records source and patch information.
7. Enables Kronos model selection inside MarketForge.

Model weights are downloaded separately from Hugging Face when first requested.

The model weights are not stored in this Git repository.

## Hardware Considerations

Kronos inference may be slow on ordinary computers.

Kronos Mini is normally the smallest available option.

Kronos Small and Base may require:

- More system memory
- Additional disk space
- Longer inference times
- A supported GPU for practical performance

The transparent MarketForge models remain available when Kronos is not installed.

---

# Desktop Packaging

Version 0.5 includes optional desktop build foundations based on PyWebView and PyInstaller.

Included files include:

```text
desktop.py
requirements-desktop.txt
marketforge-desktop.spec
scripts/build_desktop_windows.bat
scripts/build_desktop_mac_linux.sh
```

## Windows Build

```text
scripts\build_desktop_windows.bat
```

## macOS or Linux Build

```bash
chmod +x scripts/build_desktop_mac_linux.sh
./scripts/build_desktop_mac_linux.sh
```

Generated packages appear under:

```text
dist/
```

Desktop packaging depends on operating-system webview components and must be tested on the target operating system before distribution.

The repository does not claim that one desktop build will work identically across every Windows, macOS or Linux version.

---

# CSV Data Format

## Required Columns

```text
open, high, low, close
```

## Recommended Columns

```text
timestamp, volume, amount
```

## Example

```csv
timestamp,open,high,low,close,volume
2026-01-01T00:00:00Z,42000,42450,41800,42250,1250.4
2026-01-01T01:00:00Z,42250,42600,42100,42520,1184.7
2026-01-01T02:00:00Z,42520,42780,42330,42410,1092.1
```

Common aliases such as the following are recognised:

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

## Data Recommendations

For more reliable analysis:

- Use one consistent timeframe.
- Use UTC timestamps.
- Sort rows from oldest to newest.
- Avoid mixing different assets in one file.
- Include several hundred candles where possible.
- Preserve original source precision.
- Keep the original downloaded file separately.
- Inspect the quality report before forecasting.
- Confirm that evaluation data does not contain unavailable future information.

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

Real Kronos inference may require substantially more memory than the transparent MarketForge models.

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

## Core Endpoints

```text
GET    /api/health
GET    /api/engines
GET    /api/connectors
GET    /api/sample
POST   /api/import-market-data
POST   /api/analyse
POST   /api/forecast
POST   /api/backtest
POST   /api/compare
```

## Research Endpoints

```text
POST   /api/regime
POST   /api/volatility
POST   /api/stress
POST   /api/multi-asset
POST   /api/portfolio
```

## Research Workspace Endpoints

```text
GET    /api/projects
POST   /api/projects
DELETE /api/projects/{id}

GET    /api/experiments
POST   /api/experiments

GET    /api/models
POST   /api/models
```

## Reporting and Replication

```text
POST   /api/reports
POST   /api/replications/analyse
```

## Heavy-Job Limits

Forecasting, backtesting and portfolio simulations can be computationally expensive.

The server limits concurrent heavy tasks using:

```text
MARKETFORGE_MAX_CONCURRENT_JOBS
```

This reduces the risk of exhausting the host computer with too many simultaneous operations.

---

# Testing

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

Run the complete test suite:

```bash
pytest -q
```

Run tests with coverage:

```bash
pytest -q --cov=app --cov-report=term-missing --cov-fail-under=78
```

Compile-check the Python source:

```bash
python -m compileall -q app tests scripts run.py desktop.py
```

Validate browser JavaScript:

```bash
node --check app/static/app.js
```

Check the frozen benchmark:

```bash
python scripts/benchmark.py status
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

The application is tested across Python 3.10, 3.11, 3.12 and 3.13.

---

# Project Structure

```text
marketforge-ai/
├── .github/
│   ├── workflows/                # Tests, security and benchmark checks
│   └── dependabot.yml
├── app/
│   ├── api/                      # FastAPI routes
│   ├── benchmark/                # Frozen benchmark engine
│   ├── core/                     # Settings and shared schemas
│   ├── forecasting/              # Forecast models and Kronos adapter
│   ├── services/                 # Data, portfolio, storage and research tools
│   ├── static/                   # Browser interface assets
│   └── templates/                # HTML templates
├── benchmarks/
│   ├── frozen_v1/                # Superseded audit record
│   ├── frozen_v2/                # MarketForge 0.4 audit record
│   └── frozen_v3/                # Official MarketForge 0.5 protocol
├── data/                         # Sample data
├── docs/                         # Technical and beginner documentation
├── replication/                  # External ledger examples
├── scripts/                      # Install, build and benchmark tools
├── storage/                      # Local research database, excluded from Git
├── tests/                        # Automated test suite
├── vendor/                       # Optional third-party checkout location
├── desktop.py                    # Optional desktop launcher
├── marketforge-desktop.spec      # PyInstaller specification
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-dev.txt
├── requirements-desktop.txt
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

# Privacy and Security

MarketForge is designed primarily for local research workflows.

Security and privacy controls include:

- Fixed-host public exchange connectors
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
- Local SQLite storage
- Non-root Docker execution
- Dependency auditing
- CodeQL analysis

## Never Commit Sensitive Information

Do not add the following to Git:

- Exchange API keys
- Passwords
- Wallet private keys
- Wallet seed phrases
- Authentication cookies
- Private account statements
- Personal trading histories
- `.env` files
- Downloaded model weights
- `storage/marketforge.db`
- Local virtual environments
- Confidential datasets
- Personal financial information

The included `.gitignore` blocks many common sensitive or unnecessary files, but users should inspect every commit before publishing it.

Read [`SECURITY.md`](SECURITY.md) before deploying MarketForge publicly.

---

# Research Limitations

MarketForge provides tools for research—not certainty.

Important limitations include:

- Financial markets are non-stationary.
- Historical relationships can disappear.
- Models can fail during new market regimes.
- Performance can vary between assets and timeframes.
- Historical data can contain errors.
- Public model training boundaries may be uncertain.
- Simulated execution differs from live execution.
- Forecast intervals can be miscalibrated.
- Statistical significance does not guarantee profitability.
- A successful benchmark does not prove universal superiority.
- Model outputs can appear plausible while being incorrect.
- Transaction costs can remove apparent historical advantages.
- Market regimes can change without warning.
- Historical liquidity may not represent live liquidity.
- Portfolio covariance estimates can be unstable.
- Stress scenarios are assumptions rather than forecasts.
- Public exchange data may contain gaps or provider-specific conventions.
- Model performance may degrade after publication.

Users should independently verify:

- Dataset provenance
- Timestamp consistency
- Market symbol
- Candle interval
- Model revision
- Evaluation period
- Transaction-cost assumptions
- Risk calculations
- Statistical methodology
- Benchmark independence
- Whether future information entered the analysis

---

# Project Status

MarketForge AI is currently an **alpha research release**.

The following areas are implemented:

- Browser interface
- Local FastAPI server
- CSV ingestion
- Public market-data connectors
- Candle validation
- Dataset-quality reporting
- Transparent forecasting models
- Forecast calibration
- Forecast uncertainty intervals
- Walk-forward backtesting
- Matched model comparison
- Multi-asset analysis
- Portfolio simulation
- Market-regime classification
- Volatility forecasting
- Stress testing
- Saved projects
- Experiment tracking
- Model registry
- Markdown and HTML reports
- External replication analysis
- Optional Kronos adapter
- Optional desktop packaging
- Docker packaging
- Automated tests
- CodeQL analysis
- Prospective benchmark infrastructure

The prospective frozen benchmark has not yet reached its future evaluation period.

No claim is currently made that MarketForge produces more accurate forecasts than Kronos.

---

# Roadmap

Potential future improvements include:

- Additional public market-data providers
- Authenticated read-only account connectors
- Expanded exchange symbol discovery
- More transparent forecasting models
- Portfolio optimisation constraints
- Portfolio benchmark comparison
- Funding-rate and open-interest research
- Options-volatility inputs
- Market-breadth indicators
- Improved experiment comparison
- Saved chart layouts
- More report templates
- Additional calibration methods
- Expanded accessibility testing
- Complete Bulgarian translation
- Complete Spanish translation
- Additional interface languages
- Signed desktop installers
- Independent desktop security testing
- Cloud deployment documentation
- Multi-user research workspaces
- Independent benchmark replication

See [`ROADMAP.md`](ROADMAP.md) for planned development priorities.

---

# Contributing

Contributions are welcome.

Suitable contributions include:

- Bug fixes
- Automated tests
- Documentation improvements
- Accessibility improvements
- Public data connectors
- Transparent forecasting models
- Calibration tools
- Portfolio diagnostics
- Data-validation improvements
- Security hardening
- Performance improvements
- Reproducibility tools
- External replication tools

Before proposing a large change, open an issue explaining:

- The problem
- The proposed solution
- Possible research implications
- Possible security implications
- Whether frozen benchmark files would be affected

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) before submitting a pull request.

## Frozen Benchmark Changes

Do not silently modify the official benchmark v3 methodology.

Changes to benchmark-bound logic must use a new benchmark identifier and a new preregistration rather than replacing the frozen protocol.

---

# Support This Free Project

MarketForge AI is free and open-source research software.

Developing, testing, documenting and maintaining the project requires considerable time.

Donations help support:

- Continued development
- Bug fixes
- Security improvements
- Additional transparent forecasting models
- Better market-data validation
- Expanded automated testing
- Portfolio-research improvements
- Accessibility improvements
- Complete translations
- Documentation and beginner guides
- Independent benchmark research
- Development and hosting costs

Donations are completely optional.

MarketForge remains available under its open-source licence whether or not you contribute.

## Support MarketForge AI with PayPal

[![Donate securely with PayPal](https://img.shields.io/badge/Donate%20securely%20with-PayPal-0070ba?style=for-the-badge&logo=paypal&logoColor=white)](https://www.paypal.com/donate/?hosted_button_id=YE9H5NCNLWU38)

**[Support This Free Project with PayPal](https://www.paypal.com/donate/?hosted_button_id=YE9H5NCNLWU38)**

Thank you for supporting independent open-source development and responsible financial-forecasting research.

> Donations support software development. They do not purchase financial advice, investment recommendations, trading signals or guaranteed results.

---

# Third-Party Components

MarketForge AI includes optional support for the Kronos financial foundation model.

Kronos was created by its respective authors and remains a separate third-party open-source project.

MarketForge does not claim ownership of:

- The Kronos architecture
- The Kronos tokenizer
- Kronos pretrained weights
- Original Kronos research
- Third-party datasets used to train Kronos

The Kronos repository, downloaded weights and other dependencies remain subject to their own licences and attribution requirements.

See:

- [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)
- [Official Kronos repository](https://github.com/shiyu-coder/Kronos)

---

# Licence

MarketForge AI is released under the [MIT Licence](LICENSE).

You may use, copy, modify, distribute and commercially use the original MarketForge portions of this repository, subject to the MIT Licence.

Third-party source code, model weights and downloaded dependencies remain subject to their own licences.

Preserve all required copyright and attribution notices when redistributing third-party components.

---

# Acknowledgements

MarketForge AI acknowledges the researchers and developers behind:

- The Kronos financial foundation model
- PyTorch
- FastAPI
- pandas
- NumPy
- SciPy
- Hugging Face
- Plotly and browser-charting tools
- PyWebView
- PyInstaller
- Pytest
- Ruff
- CodeQL
- The wider open-source Python ecosystem

Their work makes independent financial machine-learning research more accessible.

---

# Repository

```text
https://github.com/bryanssss/marketforge-ai
```

---

# Final Notice

MarketForge AI helps users inspect market data, generate scenarios, compare forecasting models, simulate portfolios and preserve research evidence.

It cannot predict financial markets with certainty.

Always perform independent research and never risk money that you cannot afford to lose.
