# MarketForge AI 0.4 — Final Forensic Audit

**Audit date:** 24 July 2026  
**Repository:** MarketForge AI 0.4  
**Official prospective protocol:** `marketforge-prospective-v2`

## Executive verdict

MarketForge AI 0.4 is ready to publish as an **alpha research application and
prospective benchmark preregistration**. It is materially stronger than the
original Kronos repository as a complete application, evidence workflow,
backtesting environment and reproducibility package.

It is not yet scientifically valid to claim that MarketForge's forecasting
model is more accurate than Kronos. The future holdout begins on 1 August 2026,
and the software correctly blocks collection until 3 November 2026. A superiority
claim is allowed only after complete matched evidence, confidence testing and a
deterministic replay all pass.

## Critical issues found and fixed during the final audit

### 1. Hardware-dependent benchmark execution

The superseded v1 protocol used `device: auto`. The same protocol could therefore
select CPU, CUDA or Apple MPS on different computers and produce small numerical
differences.

**Fix:** prospective v2 freezes CPU-only deterministic inference, one numerical
thread, Python 3.11 and exact direct numerical/model package versions. V1 remains
preserved as an audit record and is explicitly invalid for publication.

### 2. Environment drift after protocol locking

Recording only package names in a text file does not prove that the live runtime
still matches the locked environment.

**Fix:** the benchmark now captures and verifies Python, platform, all installed
distributions, required versions, thread variables, PyTorch details and a stable
environment fingerprint. The protocol binds the resulting environment hash.

### 3. Hash-chain overclaim

A prediction hash chain detects accidental edits, but a person who can rewrite
the entire file could recompute the chain.

**Fix:** the claim gate now requires a second deterministic replay of every
forecast. The replay is compared against the original ledger field by field;
only runtime and chain-link fields are excluded.

### 4. Weak evidence-row validation

A valid row hash alone did not prove that stored actual prices, context values or
derived errors came from the frozen dataset.

**Fix:** ledger verification now reconstructs those values from canonical frozen
data and checks origins, cadence, horizons, returns, errors, direction and
interval coverage.

### 5. Data-lock verification gaps

A downloaded archive could be correct during initial collection but later be
replaced locally without a complete provider-checksum recheck.

**Fix:** the verifier rechecks every archive, provider checksum file, provider
hash, canonical CSV hash, expected symbol/month pair and duplicate timestamp.
Malformed or incomplete data is rejected rather than repaired inside the frozen
benchmark.

### 6. Statistical claim-state ambiguity

Earlier logic could blur the difference between missing evidence and completed
evidence that failed the required threshold.

**Fix:** report states are now explicit:

- `INCOMPLETE`: required tasks, origins, seeds, models or replay evidence missing;
- `FAIL`: complete evidence exists, but one or more claim gates fail;
- `PASS`: every integrity, calibration, comparator and confidence gate passes.

### 7. Naive-comparator weakness

A negative point estimate against the naive model could pass even when its
confidence interval crossed zero.

**Fix:** MarketForge must beat the naive comparator with the entire registered
95% confidence interval below zero.

### 8. Heavy API job exhaustion

Multiple simultaneous forecast, comparison or backtest requests could consume
all available CPU or GPU resources.

**Fix:** heavy endpoints now use a bounded semaphore and worker-thread execution.
The default maximum is two concurrent heavy jobs and is configurable by
environment variable.

### 9. Installer drift

A previously installed `vendor/Kronos` directory might not match the pinned
source revision.

**Fix:** installers verify that the directory is a Git checkout at the exact
registered commit, and abort on mismatch. The compatibility patch verifies its
expected source pattern, records hashes and refuses a silent patch when upstream
code differs.

### 10. Documentation and release inconsistency

Top-level documents still referred to v1 after v2 became the official protocol.

**Fix:** README, integrity policy, model-revision evidence, release checklist,
contribution guide, security policy and citation metadata now consistently
identify version 0.4 and prospective v2. Original v1 records remain unchanged.

## Verification performed

### Automated application and benchmark tests

- 42 tests passed.
- 80.14% application statement coverage.
- Coverage threshold: 78%.
- Python source compilation passed.
- Browser JavaScript syntax validation passed.
- Every JSON and YAML file parsed successfully.
- Shell scripts passed POSIX syntax validation.

### Live application smoke test

The FastAPI server started and served:

- the browser interface;
- `GET /api/health` with version `0.4.0`;
- the configured maximum of two heavy jobs;
- `nosniff`, frame denial, no-store API caching and Content Security Policy
  response headers.

### Benchmark-integrity checks

- Prospective v2 preregistration seal reproduced successfully.
- Early data collection was correctly refused.
- V1 source snapshot retained its historical code fingerprint.
- V2 code, specification, model lock and preregistration hashes verify.
- The benchmark CLI reports `PREREGISTERED — INCOMPLETE BY DESIGN`.

### Packaging checks

- Generated release manifest records every distributed file and SHA-256 hash.
- Virtual environments, caches, model weights and generated coverage files are
  excluded.
- Common credential patterns were scanned before packaging.
- The final ZIP was extracted into a clean directory and tested again.

## Frozen v2 seal

- Code SHA-256: `fcf94b3531118ad96ebfd86b44f290b2c61069d0ead7fbd153e64569614630bb`
- Specification SHA-256: `c71624e1a6c08a23e69b265189e599dbffaf12a109d1e61a29c517300983de3a`
- Model-lock SHA-256: `53e5fdb9e5681568c1b9350863f665e120246eba930483ef2227a2cb3c7816d3`
- Preregistration SHA-256: `df9846ef70f2532f73053e8705a1628fd5c41ba121857c09cc8cacdd848be4f0`

## External revision evidence checked

- Kronos source is pinned to commit
  `d5ffd46ab061af1146ea415e4ce86d24b5231b01`.
- Kronos Base is pinned to Hugging Face revision
  `2b554741eca47781b64468546e77fef3e85130e6`.
- The tokenizer, source patch and model-weight hashes are recorded separately.
- The official Kronos requirements were used to avoid introducing an unnecessary
  Transformers dependency.
- Binance's official monthly K-line archive and `.CHECKSUM` layout is the frozen
  data source.

## Honest limitations

1. **Real Kronos weights were not downloaded in this audit environment.** The
   source/revision verification, integration code and mocks were tested, but a
   full 409 MB Kronos Base inference was not executed here.
2. **Docker was unavailable in the audit container.** Dockerfile and Compose
   configuration were inspected and validated structurally, but an image build
   was not run locally.
3. **Ruff and pip-audit were unavailable from the internal package mirror.**
   Both remain mandatory GitHub Actions checks.
4. **A clean install from the internal mirror could not resolve the repository's
   July 2026 dependency versions.** Official PyPI pages confirm those releases
   exist; the limitation is the audit environment's stale mirror, not a missing
   public release.
5. **Future prospective results do not exist yet.** No scientific or marketing
   claim of superior predictive accuracy is currently permitted.
6. **CPU determinism is stronger, not mathematically universal.** Operating
   system, processor and low-level library differences are recorded, and replay
   is required, but exact floating-point identity across every future platform
   cannot be promised in advance.

## Final publication decision

Publish this exact version before the first holdout candle on **1 August 2026**.
Do not edit benchmark-bound files or replace the v2 preregistration lock under
the same benchmark ID. Improvements to the normal application can continue, but
a change to bound benchmark logic requires a new prospective protocol.

## Primary external sources

- Kronos repository and README: https://github.com/shiyu-coder/Kronos
- Kronos requirements: https://github.com/shiyu-coder/Kronos/blob/master/requirements.txt
- Kronos Base revision: https://huggingface.co/NeoQuasar/Kronos-base/commits/2b554741eca47781b64468546e77fef3e85130e6
- Binance public data: https://github.com/binance/binance-public-data
- FastAPI 0.139.2 release: https://pypi.org/project/fastapi/0.139.2/
