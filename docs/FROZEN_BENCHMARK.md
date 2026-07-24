# Prospective Frozen Benchmark v2

## Research Question

Does the frozen `marketforge-ensemble` produce lower terminal log-return forecast error than the pinned `kronos-base` comparator on future candles that did not exist when the protocol was designed?

The comparator uses the pinned official Kronos source and weights plus the disclosed MarketForge amount-preservation compatibility patch. It is not described as an unmodified upstream checkout.

## Why Version 2 Replaced Version 1

Version 1 used `device: auto`. A final pre-holdout audit found that two researchers could therefore run the same sealed benchmark on CPU, CUDA or Apple MPS and obtain slightly different numerical outputs.

Version 1 was superseded on 24 July 2026, before the first scored candle existed. No v1 result is valid for publication. Its original source snapshot and seal remain under `benchmarks/frozen_v1` for audit history.

Version 2 freezes deterministic CPU execution before the holdout begins.

## Prospective Dates

- Protocol frozen: 24 July 2026
- Holdout starts: 1 August 2026
- Holdout ends: 1 November 2026, exclusive
- Collection permitted: 3 November 2026 or later

No current superiority result exists.

## Frozen Execution Profile

The canonical run requires:

- Python 3.11
- CPU execution
- PyTorch deterministic algorithms
- One intra-op thread
- One inter-op thread
- `OMP_NUM_THREADS=1`
- `MKL_NUM_THREADS=1`
- `OPENBLAS_NUM_THREADS=1`
- `NUMEXPR_NUM_THREADS=1`
- Exact direct numerical and Kronos dependency versions from `requirements-benchmark.txt`

At protocol locking time, MarketForge records the complete installed package set, Python build, operating system, machine architecture, PyTorch configuration and thread environment. The runner compares the live environment with that record before every execution.

## Immutable Model Revisions

Kronos inference source:

```text
d5ffd46ab061af1146ea415e4ce86d24b5231b01
```

Kronos Base model:

```text
2b554741eca47781b64468546e77fef3e85130e6
```

Kronos Base tokenizer:

```text
0e0117387f39004a9016484a186a908917e22426
```

The exact weight-file SHA-256 values are stored in `benchmarks/frozen_v2/model_lock.json`. The protocol cannot be frozen until source, patch marker, model bytes and tokenizer bytes all verify.

## Frozen Data Universe

- Provider: official Binance public-data archive
- Market: spot
- Symbols: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT and XRPUSDT
- Interval: one hour
- Context begins: 1 July 2026
- Scored holdout: August through October 2026
- Forecast horizons: 1, 6 and 24 hours
- Forecast origin: 00:00 UTC daily
- Lookback: 400 candles
- Fixed seed: 78031

Each provider ZIP must match its published checksum. MarketForge also stores and later re-verifies the ZIP hash, checksum-file hash and checksum contents. Duplicate timestamps, missing candles, unexpected candles, invalid OHLC values or negative activity values cause rejection; frozen evidence is never silently repaired.

Canonical numeric values are written with 17 significant digits for float round-tripping.

## Matched Forecast Design

Each model sees the same 400 candles at the same timestamp. A single 24-hour path supplies the 1-hour, 6-hour and 24-hour endpoints. MarketForge prohibits automatic fallback during the benchmark.

Every prediction row is bound to:

- Benchmark identifier
- Dataset hash
- Protocol hash
- Environment hash
- Model and tokenizer revisions
- Origin, horizon and seed
- Previous ledger-row hash

The verifier recalculates actual prices and derived errors from the frozen canonical dataset instead of trusting values stored in the ledger.

## Full Replay Verification

A hash chain detects accidental or unrecomputed editing, but it is not a digital signature. A person who deliberately changes a row could also recompute ordinary hashes.

For that reason, v2 requires a second full execution of every model and forecast origin. MarketForge compares every deterministic evidence field from the original run with the replay. Wall-clock runtime and chain hashes are excluded because they are naturally different.

The claim gate remains `INCOMPLETE` until replay verification passes. Independent researchers can perform the same replay from the published source, locks, canonical data and model revisions.

## Statistical Evidence

Primary loss:

```text
absolute error of terminal log return
```

For each of 15 symbol–horizon tasks, the report calculates:

1. Paired candidate-minus-comparator loss differences.
2. A Diebold–Mariano test with Bartlett-weighted HAC variance.
3. A moving-block bootstrap 95% confidence interval.
4. Holm correction across one-sided task p-values.
5. A hierarchical moving-block bootstrap across tasks using relative loss differences.

Task bootstrap seeds are deterministically separated by task identifier. Random model draws are not treated as independent market observations.

## Claim Gate

“MarketForge beat Kronos on Prospective Frozen Benchmark v2” is permitted only when every requirement passes:

- All 15 tasks are complete.
- Every task has at least 75 unique matched origins.
- Every pre-registered seed is present.
- Data, model, source, environment and protocol locks verify.
- The full deterministic replay matches.
- The global hierarchical 95% confidence interval is entirely below zero.
- MarketForge wins at least two-thirds of tasks.
- At least half of tasks are Holm-significant wins with task bootstrap upper bounds below zero.
- Mean relative MAE improvement is at least 2%.
- Mean absolute central-80% coverage error is no more than 15 percentage points.
- The 95% interval against the naive sanity comparator is also entirely below zero.

Missing evidence produces `INCOMPLETE`. Complete evidence that misses a performance or integrity rule produces `FAIL`. Only complete evidence satisfying every rule produces `PASS`.

## Commands

Check the seal now:

```bash
python scripts/benchmark.py status
python scripts/benchmark.py preregister
```

Create the dedicated environment before the future run:

```bash
./scripts/setup_benchmark_env_mac_linux.sh
```

After 3 November 2026:

```bash
python scripts/benchmark.py freeze-data
python scripts/benchmark.py verify-models --download-weights
python scripts/benchmark.py verify-environment
python scripts/benchmark.py lock-protocol
python scripts/benchmark.py run --models marketforge-naive,marketforge-ensemble,kronos-base
python scripts/benchmark.py verify-results --models marketforge-naive,marketforge-ensemble,kronos-base
python scripts/benchmark.py report --candidate marketforge-ensemble --comparator kronos-base
```

## Interpretation

A `PASS` supports a narrow statement about these exact models, symbols, dates, horizons and metrics. It does not prove live-trading profitability, universal superiority or guaranteed future performance.
