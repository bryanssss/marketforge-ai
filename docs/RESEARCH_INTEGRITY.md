# Research Integrity Policy

MarketForge is designed to make accidental or selective reporting harder.

## Claims We Do Not Make

- Forecasts are not guaranteed.
- Backtests are not live trading results.
- A higher historical return does not prove future profitability.
- Kronos historical tests are not labelled clean out-of-sample without a verified training cut-off.
- An uncertainty interval is not called calibrated until matched rolling-origin evidence supports it.
- A model registry entry does not prove that a model is safe, accurate or independently reviewed.
- External replication analysis cannot prove that the submitted dataset is genuinely independent.

## Required Evaluation Order

1. Choose the hypothesis, assets, dates and metrics before inspecting the final result.
2. Keep training, validation and final test periods chronological.
3. Fit normalisers, calibration rules and thresholds on past information only.
4. Include naive and transparent statistical baselines.
5. Generate the signal before the simulated entry price becomes available.
6. Include fees, spread or slippage and realistic position constraints.
7. Retain forecasts that did not become trades.
8. Report every market and horizon tested, not only successful configurations.
9. Freeze the final test set and avoid repeated tuning against it.
10. Record dataset fingerprints, settings, seeds, software versions and model revisions.
11. Separate forecast evidence from trading-strategy evidence.
12. Publish `INCOMPLETE` and `FAIL` outcomes as readily as `PASS` outcomes.

## Public Market-Data Connectors

Public connectors are conveniences, not trusted or immutable research sources. Before
publishing results, record the provider, request parameters, retrieval time, raw payload
hash and canonical dataset hash. Provider APIs may revise recent candles, impose limits
or temporarily return incomplete information.

The frozen benchmark does not rely on live API responses. It uses official archived
files and provider checksums.

## Saved Projects, Experiments and Model Records

Local projects, experiment records and model-registry entries are research metadata.
They are not cryptographic evidence by themselves. Important results should additionally
include immutable exports, source revisions and dataset fingerprints.

Do not register or execute arbitrary third-party Python code merely because it appears
in the local model registry. The registry records metadata; it is not a plug-in trust
system.

## Kronos Status

The optional public Kronos models are useful research engines. MarketForge records their
model name, revision, device and draw count. Until a reliable public training cut-off is
available, historical Kronos results retain this status:

```text
unverified-training-cutoff
```

## Responsible Publication Checklist

Before publishing a performance result, include:

- data source and licence;
- asset universe and selection rules;
- exact date range, interval and timezone;
- raw and canonical data fingerprints;
- model, code and dependency revisions;
- forecast horizon and evaluation frequency;
- calibration method;
- transaction-cost assumptions;
- benchmark definition;
- forecast metrics as well as trading metrics;
- uncertainty or confidence intervals;
- all failed and excluded configurations;
- limitations and possible leakage risks.

## Prospective Frozen Benchmark v3

The official protocol under `benchmarks/frozen_v3` operationalises this policy for
MarketForge AI 0.5. Exact candidate and comparator revisions predate all scored candles,
official archive checksums are required, deterministic replay is mandatory, and the
final claim gate was encoded before results existed.

Version 2 remains the public MarketForge AI 0.4 record. Version 3 was created rather
than modifying v2 because the 0.5 forecasting system changed before the holdout began.
Any later methodological change requires another benchmark identifier and documented
supersession; it must not overwrite v3.
