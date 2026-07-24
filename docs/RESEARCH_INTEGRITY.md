# Research Integrity Policy

MarketForge is designed to make it harder to accidentally report a misleading result.

## Claims We Do Not Make

- Forecasts are not guaranteed.
- Backtests are not live trading results.
- A higher historical return does not prove future profitability.
- Kronos historical tests are not labelled clean out-of-sample without a verified training cut-off.
- An uncertainty interval is not called calibrated until rolling-origin evidence supports it.

## Required Evaluation Order

1. Choose the hypothesis and metrics before inspecting the test result.
2. Keep train, validation and final test dates chronological.
3. Fit normalisers and thresholds on past information only.
4. Include naive and simple statistical baselines.
5. Generate the signal before the simulated entry price becomes available.
6. Include fees, spread/slippage and realistic position constraints.
7. Retain forecasts that did not become trades.
8. Report all markets and horizons tested, not only the best ones.
9. Freeze the final test set and avoid repeated tuning against it.
10. Record data fingerprints, settings, seeds and model revisions.

## Kronos Status

The optional public Kronos models are useful research engines. MarketForge records their model name, device, draw count and an out-of-sample status. Until a reliable training cut-off is available, the status remains:

```text
unverified-training-cutoff
```

## Responsible Publication Checklist

Before publishing a performance result, include:

- data source and licence;
- asset universe and selection rules;
- exact date range and timezone;
- data fingerprint;
- model and code revision;
- forecast horizon and rebalance frequency;
- transaction cost assumptions;
- benchmark definition;
- forecast metrics as well as trading metrics;
- uncertainty or confidence intervals;
- limitations and failed configurations.

## Prospective Frozen Benchmark v2

The benchmark under `benchmarks/frozen_v2` operationalises this policy. Its exact model revisions predate all benchmark candles, official archive checksums are required, and the final claim gate is encoded before results are generated.

The repository must publish `INCOMPLETE` or `FAIL` results as readily as `PASS` results. Changing the benchmark after viewing results requires a new benchmark identifier and a documented new protocol; it must not overwrite Prospective Frozen Benchmark v2. The preserved v1 protocol remains an audit record of the superseded pre-holdout design.
