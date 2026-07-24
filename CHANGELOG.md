# Changelog

## 0.5.0 — 2026-07-24 — Research workbench expansion

### Added

- Read-only public candle connectors for Binance Spot, Coinbase Exchange and Kraken Spot.
- Direct exchange-data import in the browser interface.
- Exponential-smoothing, momentum, mean-reversion and regime-aware ensemble models.
- Empirical and widen-only conformal forecast-interval calibration.
- Market-regime classification and volatility forecasting.
- Scenario stress testing with VaR and expected-shortfall summaries.
- Multi-asset correlation analysis and portfolio simulation.
- Equal-weight, inverse-volatility, risk-parity and minimum-variance allocation.
- Local saved projects, experiment tracking and model registry using SQLite.
- Executive, research, risk and model-card reports.
- External benchmark-replication ledger analyser and command-line tool.
- Optional PyWebView/PyInstaller desktop packaging.
- English, Bulgarian and Spanish interface foundations.
- High-contrast, reduced-motion and accessible chart-table support.
- Expanded backtest diagnostics including trade VaR, expected shortfall, ulcer index, recovery factor, Omega ratio, skewness, kurtosis and streaks.
- Prospective Frozen Benchmark v3 for the v0.5 regime-aware candidate.

### Changed

- The recommended transparent model is now `regime_ensemble`.
- The benchmark command defaults to `benchmarks/frozen_v3`.
- Benchmark v2 remains preserved as the public v0.4 audit record.
- The browser interface now includes Forecast, Backtest, Portfolio and Research Lab modes.

### Verification

- 57 automated tests pass.
- Application coverage remains above the required 78% threshold.
- Python compilation and browser JavaScript syntax checks pass.
- Prospective v3 preregistration verifies and data collection remains blocked until 3 November 2026.

## 0.4.1 — 2026-07-24 — GitHub Actions hotfix

- Updated checkout and Python setup actions to Node 24-compatible major versions.
- Updated CodeQL from v3 to v4.
- Changed the dependency audit to scan only declared application dependencies instead of the complete runner environment.
- Limited pull-request audits to relevant application dependency files.
- Excluded frozen benchmark and Kronos compatibility manifests from automatic Dependabot version changes.
- Kept the preregistered benchmark v2 source and seal unchanged.

## 0.4.0 — 2026-07-24 — Final forensic audit

- Superseded prospective v1 before holdout and preregistered deterministic v2.
- Pinned CPU, single-thread execution and exact numerical package versions.
- Added execution-environment lock and stronger source-code fingerprint.
- Added archive/checksum re-verification and duplicate-candle rejection.
- Added ledger bindings to protocol, environment and dataset hashes.
- Fixed claim gate to distinguish INCOMPLETE from FAIL.
- Strengthened naive comparator requirement to a full 95% confidence interval.
- Added API heavy-job concurrency limiting and strict no-fallback benchmark checks.

## 0.3.0 — 2026-07-23

### Added

- Prospective Frozen Benchmark v1 with pre-registered assets, dates, horizons, seeds and claim thresholds. This protocol was later superseded before its holdout began; its files remain preserved for auditability.
- Official Binance archive download and provider-checksum verification.
- Canonical dataset hashing and protocol locks binding data, models, spec and Git state.
- Exact Kronos source, model and tokenizer revision locks with weight SHA-256 values.
- Matched-origin resumable prediction ledger with an append-only SHA-256 hash chain.
- Diebold–Mariano tests with HAC variance, moving-block bootstrap confidence intervals, Holm correction and hierarchical bootstrap.
- Strict PASS/FAIL claim gate after complete evidence; missing prospective evidence remains unreportable and is shown as INCOMPLETE by benchmark status.
- One-click Windows and macOS/Linux benchmark launchers.
- Benchmark protocol, model-lock verification and expanded automated tests.

### Changed

- Optional Kronos installation now defaults to an immutable source commit instead of `master`.
- Kronos model loading accepts immutable model and tokenizer revisions.
- Release version raised to 0.3.0.

## 0.2.0 — 2026-07-23

### Added

- Moving-block, drift, naive and ensemble baseline engines.
- Independent Kronos draws with empirical uncertainty quantiles.
- Thread-safe lazy Kronos model cache.
- Explicit fallback metadata.
- UTC normalisation, gap estimates, outlier detection and data fingerprints.
- Amount inference and a reversible Kronos amount-preservation patch.
- Next-open walk-forward execution with costs, stops, targets and no-overlap default.
- Forecast calibration metrics and buy-and-hold comparison.
- `/api/compare` matched baseline leaderboard.
- Request IDs, trusted hosts and browser security headers.
- Hardened non-root Docker configuration.
- Dependabot, CodeQL, dependency audit and four-version CI.
- Installation doctor and expanded documentation.
- 25 automated tests with 81% coverage in the review environment.

### Changed

- Hosted privacy wording now distinguishes server upload from local use.
- Backtests are explicitly baseline-only until a verifiable Kronos training cut-off is available.
- Upload errors are sanitised and resource limits are enforced.

### Security

- Raised `python-multipart` above the version affected by CVE-2026-42561.
