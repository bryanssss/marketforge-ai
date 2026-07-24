# MarketForge AI 0.5 Release Audit

**Release:** 0.5.0  
**Audit date:** 24 July 2026  
**Official prospective protocol:** `marketforge-prospective-v3`

## Scope

This audit covers the 0.5 research-workbench expansion, its interaction with existing
forecasting and backtesting code, and the replacement of roadmap promises with tested
features.

## Implemented Capabilities

### Public Market Data

- Read-only Binance, Coinbase and Kraken connectors
- Exchange-specific symbol and interval normalisation
- Request timeouts and response-size protection
- Canonical UTC OHLCV conversion
- Ordinary MarketForge data-quality validation after import

### Forecasting

- Naive persistence
- Robust drift
- Moving-block bootstrap
- Exponential smoothing
- Momentum
- Mean reversion
- Original ensemble
- Regime-aware ensemble
- Empirical and conformal-style interval calibration

### Research Lab

- Interpretable regime classification
- EWMA, Parkinson and Garman–Klass volatility estimates
- Combined volatility forecast
- Historical and synthetic stress scenarios
- Markdown report templates
- External paired-result replication analysis

### Portfolio and Multi-Asset Research

- Timestamp-aligned multi-asset analysis
- Correlation and covariance matrices
- Equal-weight and risk-parity-style allocations
- Rebalancing simulation
- Concentration, drawdown and return diagnostics

### Workflow and Packaging

- Local SQLite projects
- Experiment records
- Model metadata registry
- Desktop wrapper and platform build scripts
- English, Bulgarian and Spanish interface foundation
- High-contrast and reduced-motion controls
- Chart range controls and accessible data table

## Important Design Boundaries

- Public connectors do not place trades and do not accept secret exchange credentials.
- The model registry stores metadata; it does not execute arbitrary plug-ins.
- Saved projects are local metadata records, not complete immutable research archives.
- External replication analysis verifies paired calculations, not the submitter's
  independence or data provenance.
- Desktop executables must be built and tested on each target operating system.
- Public API provider availability cannot be guaranteed by MarketForge.

## Benchmark Integrity Decision

MarketForge AI 0.5 changed the candidate forecasting system after prospective v2 had
been published. Replacing the v2 candidate in place would have broken the public research
record.

The release therefore preserves v2 and preregisters prospective v3 with:

- candidate `marketforge-regime-ensemble`;
- empirical central-80% interval calibration;
- the same future August–October 2026 holdout;
- deterministic CPU execution;
- exact source and model hashes;
- matched forecast origins;
- deterministic replay;
- statistical claim gates.

The command-line defaults and one-click scripts were reviewed to ensure they run the
complete registered v3 model list and report the registered candidate.

## Automated Verification

The final release process requires:

```text
Python compilation
57 automated tests
at least 78% application coverage
browser JavaScript syntax validation
critical production Ruff checks
prospective v3 seal verification
JSON and YAML validation
release-manifest verification
clean ZIP extraction and retest
```

## Remaining External Verification

The following cannot be fully established in a network-restricted build environment:

- live responses from all public exchanges at release time;
- actual download and inference with every Kronos weight set;
- platform-specific desktop executable behaviour;
- Docker image execution when Docker is unavailable;
- future prospective benchmark results.

These limitations must remain visible in release notes.

## Verdict

MarketForge AI 0.5 converts the listed 0.4 roadmap items into a coherent research
workbench. It is suitable for an alpha prerelease, not for financial advice, unattended
trading or claims of proven model superiority.
