# MarketForge AI Deep Code Review

**Review date:** 24 July 2026  
**Reviewed:** MarketForge AI 0.1–0.4 and the public Kronos repository  
**Verdict:** MarketForge AI can be a materially stronger **application and research workflow** than the original Kronos repository. It cannot honestly be called a better foundation model until independent, uncontaminated forecasting benchmarks demonstrate that.

## Executive Decision

Build MarketForge as an evidence-aware product around transparent baselines and optional Kronos inference. Do not compete by claiming that a polished dashboard makes the underlying model more accurate. Compete on:

- safer data ingestion;
- reproducible uncertainty estimates;
- realistic chronological evaluation;
- transparent fallback and provenance;
- model comparison against naive baselines;
- deployment security;
- documentation and tests.

Kronos remains the third-party model research component. MarketForge is the application, validation and evidence layer.

## Research Findings That Changed the Design

### 1. A clean Kronos out-of-sample period is not currently verifiable

A public Kronos issue asks the authors to disclose the pretraining cut-off so downstream researchers can identify a genuinely untouched test window. Another issue reported future-information leakage in a dataset normalisation path. Those concerns do not prove every Kronos forecast is contaminated, but they mean MarketForge must not label a historical Kronos evaluation “clean out-of-sample” without verified model and data cut-offs.

**Decision:** Kronos backtesting is disabled in the trustworthy baseline backtest. Every Kronos result carries `oos_status: unverified-training-cutoff` until evidence is supplied.

### 2. Direct Kronos `sample_count` output is an average, not a distribution

The public predictor repeats samples and averages them before returning. Using one returned prediction as both lower and upper uncertainty bounds is therefore invalid.

**Decision:** MarketForge requests `sample_count=1` repeatedly with independent seeds, validates every draw, and builds quantiles across those separate draws.

### 3. Current upstream amount handling can overwrite supplied amount data

The public predictor source assigns the amount column to zero before checking whether the amount column is absent. That can discard real amount/turnover data.

**Decision:** MarketForge now:

1. estimates amount from volume and typical price when the upload omits it;
2. includes a small, explicit compatibility patcher for an installed Kronos checkout;
3. backs up the original source;
4. records the upstream commit and patch identifier;
5. fails safely when the expected upstream pattern has changed.

### 4. The original Kronos backtest is explicitly a demonstration

The Kronos README itself says its fine-tuning/backtesting pipeline is simplified and not production-ready. It calls out the need for more sophisticated portfolio and risk treatment.

**Decision:** MarketForge describes all results as research simulations and adds execution timing, costs, no-overlap defaults, conservative stop handling and benchmark comparisons.

## Audit Findings and Repairs

| Severity | Previous problem | Risk | MarketForge 0.2 repair |
|---|---|---|---|
| Critical | Signal and entry could use the same completed close | Trade-on-close look-ahead | Signals use completed history; entry is a later candle open |
| Critical | Overlapping trades could reuse the same capital | Inflated compound return | Overlap disabled by default and disclosed when enabled |
| Critical | Kronos historical purity unknown | False out-of-sample claims | Explicit unverified cut-off status and no clean-OOS label |
| High | Kronos sample paths were averaged internally | False or collapsed uncertainty | Independent one-sample draws and empirical quantiles |
| High | Upstream amount column can be zeroed | Lost model input information | Safe compatibility patch with backup and provenance record |
| High | Any Kronos failure silently became a baseline result | Users could misunderstand the engine | Fallback object displayed in API and interface |
| High | Model/tokenizer loaded on every request | Large delay and memory churn | Thread-safe lazy cache per model and device |
| High | CPU/GPU inference executed in async request loop | Server responsiveness loss | Forecasting and backtesting run in a worker thread |
| High | Old upload parser dependency was below a 2026 security fix | Multipart denial of service exposure | Secure dependency floor plus request/file limits and audit workflow |
| High | Docker process ran as root | Larger container blast radius | Non-root user, dropped capabilities, read-only filesystem and health check |
| Medium | Independent return shuffling removed temporal dependence | Unrealistic path shapes | Moving-block sampling of gap/body/wicks/volume features |
| Medium | No naive benchmark | Complex model could look good without earning it | Naive, drift, block and ensemble comparison endpoint |
| Medium | No interval calibration report | Wide intervals could masquerade as quality | Coverage and average interval width reported |
| Medium | No-trade forecasts disappeared from strategy evidence | Selective reporting | Every forecast is included in accuracy statistics |
| Medium | Raw parser/model errors could reach users | Information leakage and poor UX | Safe domain errors and request IDs |
| Medium | Timestamp gaps and duplicate rows were mostly hidden | Misleading intervals | UTC conversion, deduplication, gap estimates, outlier checks and fingerprint |
| Medium | Hosted privacy wording could imply local processing | Misleading privacy claim | UI distinguishes local mode from hosted uploads |
| Low | Two tests and one Python version in CI | Regressions likely | 25 tests, 81% coverage and four-Python-version CI matrix |

## New Forecasting Layer

The transparent baseline is now a family of four models:

- **Naive:** near-persistence with small empirically scaled shocks;
- **Robust drift:** recent robust drift plus volatility shocks;
- **Moving-block bootstrap:** resamples contiguous candle-feature blocks;
- **Ensemble:** combines the three path distributions.

Each generated candle preserves:

- positive prices;
- `high >= max(open, close)`;
- `low <= min(open, close)`;
- non-negative volume and amount;
- deterministic reproduction when the seed is unchanged.

This is not marketed as a new foundation model. It is a transparent benchmark and scenario generator.

## New Backtesting Layer

The 0.2 backtest uses rolling-origin evaluation:

1. reveal only history available at the signal time;
2. generate a forecast;
3. retain the forecast in accuracy metrics even when no trade is opened;
4. wait for the configured execution delay;
5. enter at the later candle open;
6. apply fees and slippage on both sides;
7. resolve gaps and intrabar stop/target events;
8. choose the stop when both stop and target occur in the same candle;
9. prevent capital overlap by default;
10. compare with a cost-adjusted buy-and-hold benchmark.

Reported forecast evidence includes MAE, RMSE, directional accuracy, central-80% interval coverage and average interval width. Strategy evidence includes return, benchmark excess, win rate, drawdown, profit factor, expectancy, payoff and exposure.

## Security Review

MarketForge 0.2 adds:

- upload size, request size, row and column limits;
- content-type and extension checks;
- null-byte rejection;
- sanitised parser errors;
- trusted host validation;
- CSP, frame, MIME, referrer and permissions headers;
- request IDs without echoing unsafe arbitrary values;
- API no-store caching;
- non-root, read-only Docker execution;
- Dependabot, CodeQL and weekly dependency audit workflows;
- model weights, virtual environments and private outputs excluded from Git.

## Test Evidence

The review build passed:

- Python compilation for application, scripts and tests;
- 25 automated tests;
- 81.39% Python statement coverage;
- JavaScript syntax validation with Node.js;
- application dependency/self-check diagnostics.

The real Kronos weights were not downloaded in the review environment, so GPU/CPU inference against the official model files remains an integration test for a machine with the optional Kronos dependencies installed.

## Can It Be “Better Than Kronos”?

### Yes, in these dimensions

- product usability;
- data quality reporting;
- uncertainty presentation;
- honest model fallback;
- reproducibility metadata;
- backtest execution realism;
- baseline comparison;
- web/API security;
- deployment packaging;
- tests and contributor workflow.

### Not yet proven in these dimensions

- raw forecast accuracy;
- cross-market generalisation;
- volatility prediction;
- synthetic-data fidelity;
- trading profitability;
- GPU throughput versus upstream batch inference.

A claim of superior prediction requires a pre-registered benchmark on untouched data after a known training cut-off, with costs, multiple markets, several horizons, statistical confidence intervals and all failed experiments retained.

## Recommended Next Research Milestones

1. Obtain or independently establish Kronos model cut-off evidence.
2. Create frozen post-cut-off benchmark datasets with licences and hashes.
3. Add batch evaluation without allowing future-window normalisation.
4. Add Diebold–Mariano or block-bootstrap confidence testing for forecast differences.
5. Add regime-stratified results and calibration plots.
6. Add a true event-driven multi-position portfolio engine before enabling overlapping capital as a standard mode.
7. Add a model registry with immutable model revision hashes.
8. Benchmark the compatibility-patched Kronos adapter against the unpatched upstream version.
9. Add browser end-to-end tests and actual Docker build tests in CI.
10. Only then investigate a proprietary tokenizer or model.

## Primary Sources

- Kronos repository and model zoo: https://github.com/shiyu-coder/Kronos
- Kronos paper: https://arxiv.org/abs/2508.02739
- Dataset leakage report: https://github.com/shiyu-coder/Kronos/issues/227
- Training cut-off clarification request: https://github.com/shiyu-coder/Kronos/issues/265
- Public predictor implementation: https://raw.githubusercontent.com/shiyu-coder/Kronos/refs/heads/master/model/kronos.py
- Multipart parser advisory: https://advisories.gitlab.com/pypi/python-multipart/CVE-2026-42561/
