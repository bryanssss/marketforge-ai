# Prospective Frozen Benchmark v3

## Purpose

Prospective Frozen Benchmark v3 is the official MarketForge AI 0.5 research protocol.
It asks one deliberately narrow question:

> Does the frozen `marketforge-regime-ensemble` produce lower terminal log-return
> error than the pinned `kronos-base` comparator on future, matched market candles?

The protocol was frozen before the first scored candle existed. It therefore contains
no result today and makes no superiority claim.

## Why Version 3 Exists

Version 2 remains the published MarketForge AI 0.4 audit record. Version 3 was created
before the holdout began because MarketForge AI 0.5 introduced a materially different
forecasting system:

- regime-aware model selection;
- an additional regime ensemble;
- explicit empirical interval calibration;
- expanded model metadata and diagnostics;
- a broader research workbench.

Changing the candidate after a protocol is published would invalidate the old seal.
MarketForge therefore created a new benchmark identifier instead of rewriting v2.

## Prospective Dates

- Protocol frozen: 24 July 2026
- Holdout starts: 1 August 2026
- Holdout ends: 1 November 2026, exclusive
- Collection permitted: 3 November 2026 or later

Current status:

```text
PREREGISTERED — INCOMPLETE BY DESIGN
```

## Registered Models

Primary candidate:

```text
marketforge-regime-ensemble
```

Primary comparator:

```text
kronos-base
```

Sanity comparator:

```text
marketforge-naive
```

Additional registered reference:

```text
marketforge-ensemble
```

The candidate uses the exact MarketForge AI 0.5 implementation bound by the
preregistration code fingerprint. Kronos uses a pinned source commit, compatibility
patch, model revision and tokenizer revision recorded in
`benchmarks/frozen_v3/model_lock.json`.

## Frozen Execution Profile

The canonical run requires:

- Python 3.11;
- CPU-only inference;
- deterministic PyTorch algorithms;
- one intra-op and one inter-op numerical thread;
- `OMP_NUM_THREADS=1`;
- `MKL_NUM_THREADS=1`;
- `OPENBLAS_NUM_THREADS=1`;
- `NUMEXPR_NUM_THREADS=1`;
- exact direct numerical and model dependencies from `requirements-benchmark.txt`;
- empirical interval calibration;
- a central 80% forecast interval.

The runner records and verifies the Python build, operating system, architecture,
installed packages, PyTorch configuration and thread environment.

## Frozen Model Revisions

Kronos inference source commit:

```text
d5ffd46ab061af1146ea415e4ce86d24b5231b01
```

Kronos Base revision:

```text
2b554741eca47781b64468546e77fef3e85130e6
```

Kronos Base tokenizer revision:

```text
0e0117387f39004a9016484a186a908917e22426
```

Exact weight hashes and MarketForge candidate revisions are stored in
`benchmarks/frozen_v3/model_lock.json`. A newer source checkout or model revision is
not silently substituted.

## Frozen Data Universe

- Provider: official Binance public-data archives
- Market: spot
- Symbols: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT and XRPUSDT
- Interval: one hour
- Context begins: 1 July 2026
- Scored holdout: August through October 2026
- Forecast horizons: 1, 6 and 24 hours
- Forecast origin: 00:00 UTC daily
- Lookback: 400 candles
- Registered seed: 78031

Each provider archive must match its published checksum. MarketForge records and later
re-verifies archive hashes, checksum-file hashes and canonical dataset hashes.
Duplicate timestamps, missing candles, invalid OHLC values or negative activity values
cause rejection; frozen evidence is never silently repaired.

## Matched Forecast Design

Every model sees the same 400 historical candles at the same timestamp. One generated
24-hour path supplies the 1-hour, 6-hour and 24-hour endpoints. Automatic model fallback
is forbidden during the benchmark.

Each evidence row is bound to:

- benchmark identifier;
- dataset fingerprint;
- protocol and environment hashes;
- model and tokenizer revisions;
- forecast origin, horizon and seed;
- previous ledger-row hash.

The verifier reconstructs actual prices and errors from the frozen canonical dataset
instead of trusting stored derived values.

## Deterministic Replay

A hash chain detects accidental or unrecomputed editing, but it is not a digital
signature. Version 3 therefore requires a second complete execution of every model,
symbol and origin before a claim can pass.

The replay compares all deterministic evidence fields. Wall-clock runtime and chain
hashes are excluded because they naturally differ. A mismatch leaves the claim gate
incomplete or failed.

## Statistical Evidence

Primary loss:

```text
absolute error of terminal log return
```

For each of 15 symbol–horizon tasks, the report calculates:

1. paired candidate-minus-comparator loss differences;
2. a Diebold–Mariano test with Bartlett-weighted HAC variance;
3. a moving-block bootstrap 95% confidence interval;
4. Holm correction across one-sided task p-values;
5. a hierarchical moving-block bootstrap across tasks using relative loss differences.

Generated model paths are used to estimate uncertainty; they are not counted as
independent market observations.

## Claim Gate

“MarketForge beat Kronos on Prospective Frozen Benchmark v3” is permitted only when
all registered integrity and performance requirements pass:

- all 15 tasks are complete;
- every task has at least 75 unique matched origins;
- every registered seed is present;
- data, model, source, environment and protocol locks verify;
- the complete deterministic replay matches;
- the global hierarchical 95% confidence interval is entirely below zero;
- MarketForge wins at least two-thirds of tasks;
- at least half of tasks are Holm-significant wins with bootstrap upper bounds below zero;
- mean relative MAE improvement is at least 2%;
- mean absolute central-80% coverage error is no more than 15 percentage points;
- the 95% interval against the naive comparator is also entirely below zero.

Result meanings:

```text
INCOMPLETE = required evidence is missing
FAIL       = complete evidence misses one or more registered rules
PASS       = every registered rule passes
```

## Commands

Verify the public seal now:

```bash
python scripts/benchmark.py status
python scripts/benchmark.py preregister
```

Create the dedicated benchmark environment:

```bash
./scripts/setup_benchmark_env_mac_linux.sh
```

After 3 November 2026:

```bash
python scripts/benchmark.py freeze-data
python scripts/benchmark.py verify-models --download-weights
python scripts/benchmark.py verify-environment
python scripts/benchmark.py lock-protocol
python scripts/benchmark.py run --models marketforge-naive,marketforge-ensemble,marketforge-regime-ensemble,kronos-base
python scripts/benchmark.py verify-results --models marketforge-naive,marketforge-ensemble,marketforge-regime-ensemble,kronos-base
python scripts/benchmark.py report --candidate marketforge-regime-ensemble --comparator kronos-base
```

Windows and macOS/Linux helper scripts are available under `scripts/`.

## Interpretation

A `PASS` would support only a narrow statement about these exact models, assets, dates,
horizons, data rules and metrics. It would not prove live-trading profitability,
universal model superiority or guaranteed future performance.

Version 2 remains available in `benchmarks/frozen_v2` and
`docs/FROZEN_BENCHMARK_V2.md` as a public historical record.
