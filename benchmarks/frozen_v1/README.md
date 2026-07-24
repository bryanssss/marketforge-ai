# MarketForge Prospective Frozen Benchmark v1

This is a pre-registered prospective benchmark, not a selected historical demo.

## Current status

- Protocol design date: 23 July 2026
- First scored candle: 1 August 2026
- Last scored candle: 31 October 2026
- Earliest complete data collection: 3 November 2026
- Current result: **INCOMPLETE BY DESIGN**

The future holdout is deliberate. At the time the code, models, assets, metrics and pass rules are frozen, none of the scored candles exists.

## Frozen comparison

Candidate: `marketforge-ensemble`

Primary comparator: `kronos-base`

Sanity comparator: `marketforge-naive`

The benchmark uses five Binance spot pairs, one-hour candles, 1/6/24-hour horizons and one daily forecast origin. All horizons are taken from the same 24-hour forecast path. One fixed seed is used; statistical uncertainty comes from independent future origins rather than pretending repeated random seeds are extra market observations.

## Before 3 November 2026

```bash
python scripts/benchmark.py status
python scripts/benchmark.py preregister
```

Both commands should confirm that the preregistration lock is intact and the prospective data remains sealed.

## After the holdout is complete

```bash
python scripts/benchmark.py freeze-data
python scripts/benchmark.py verify-models --download-weights
python scripts/benchmark.py lock-protocol
python scripts/benchmark.py run --models marketforge-naive,marketforge-ensemble,kronos-base
python scripts/benchmark.py report --candidate marketforge-ensemble --comparator kronos-base
```

The runner writes an append-only, hash-chained prediction ledger and resumes without repeating completed model calls.

A superiority statement is blocked unless every pre-registered rule passes. A `PASS` applies only to this exact benchmark and is not a promise of profit or future performance.
