# Model Revision Evidence — Prospective Frozen Benchmark v3

This document explains the external and internal revisions bound by
`benchmarks/frozen_v3/model_lock.json`. The JSON lock is authoritative.

## MarketForge Candidate

- Model identifier: `marketforge-regime-ensemble`
- Implementation: `app.services.forecast_service`
- Revision label: `marketforge-ai-0.5.0`
- Calibration: `empirical`
- Source fingerprint: recorded in `benchmarks/frozen_v3/preregistration_lock.json`

The candidate implementation cannot be changed under the same benchmark identifier.
A source change requires a new protocol and new seal.

## MarketForge Reference Models

- `marketforge-naive`
- `marketforge-ensemble`

Both are pinned to the same MarketForge AI 0.5 source fingerprint.

## Kronos Inference Source

- Repository: `https://github.com/shiyu-coder/Kronos`
- Commit: `d5ffd46ab061af1146ea415e4ce86d24b5231b01`
- Compatibility patch: `marketforge-preserve-kronos-amount-v1`

The installer checks out the exact commit rather than a moving branch. The compatibility
patch records original and patched file hashes and refuses to continue when the expected
upstream source pattern is absent.

## Kronos Base

- Hugging Face repository: `NeoQuasar/Kronos-base`
- Revision: `2b554741eca47781b64468546e77fef3e85130e6`
- `model.safetensors` SHA-256:
  `abff193acab6db1a0368e9773e75799d11403b6d054ee6d5f0a11aeabc5f4b83`

## Kronos Base Tokenizer

- Hugging Face repository: `NeoQuasar/Kronos-Tokenizer-base`
- Revision: `0e0117387f39004a9016484a186a908917e22426`
- `model.safetensors` SHA-256:
  `59d85f6af76a2c3b8240ea06cb21db4213b4eeca053f246b23e29cf832fc6bee`

## Additional Optional Kronos Revisions

The model lock also records Kronos Mini, Kronos Small and the 2k tokenizer for
application reproducibility. They are not the primary v3 comparator unless the benchmark
specification explicitly names them.

## Verification Command

After installing optional Kronos support, run:

```bash
python scripts/benchmark.py verify-models --download-weights
```

A model is accepted only when the exact source commit, compatibility patch, repository
revision, tokenizer revision and local weight hashes verify. A newer model is not
silently substituted.

## Scope of the Evidence

The lock proves which bytes and source revisions were evaluated. It does not prove that
a model is accurate, safe or profitable. It also does not independently reveal the full
Kronos training corpus. The prospective design addresses historical contamination by
using scored candles that begin after this protocol was frozen.
