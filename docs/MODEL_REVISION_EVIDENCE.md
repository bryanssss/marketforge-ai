# Model Revision Evidence — Prospective Frozen Benchmark v2

This record explains which external revisions are bound by
`benchmarks/frozen_v2/model_lock.json`. The JSON lock is authoritative.

## Kronos inference source

- Repository: `https://github.com/shiyu-coder/Kronos`
- Commit: `d5ffd46ab061af1146ea415e4ce86d24b5231b01`
- Selected before the prospective holdout.
- MarketForge compatibility patch: `marketforge-preserve-kronos-amount-v1`

The installer checks out the exact commit rather than a moving branch. The
compatibility patch records the original and patched file hashes and refuses to
continue when the expected upstream source pattern is absent.

## Kronos Base

- Hugging Face repository: `NeoQuasar/Kronos-base`
- Revision: `2b554741eca47781b64468546e77fef3e85130e6`
- `model.safetensors` SHA-256:
  `abff193acab6db1a0368e9773e75799d11403b6d054ee6d5f0a11aeabc5f4b83`

## Kronos Base tokenizer

- Hugging Face repository: `NeoQuasar/Kronos-Tokenizer-base`
- Revision: `0e0117387f39004a9016484a186a908917e22426`
- `model.safetensors` SHA-256:
  `59d85f6af76a2c3b8240ea06cb21db4213b4eeca053f246b23e29cf832fc6bee`

## Verification command

After installing the optional Kronos integration, run:

```bash
python scripts/benchmark.py verify-models --download-weights
```

A model is usable for the frozen benchmark only when the exact source commit,
compatibility patch, model revision, tokenizer revision and local weight hashes
all verify. A newer model is not silently substituted.

## Scope

The lock proves which bytes were evaluated. It does not prove that the model's
training corpus excludes every benchmark period. The prospective holdout solves
that problem by using candles beginning after this protocol was frozen.
