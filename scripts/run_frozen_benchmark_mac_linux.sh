#!/usr/bin/env sh
set -eu
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
cd "$(dirname "$0")/.."

if [ ! -x .venv-benchmark/bin/python ]; then
  echo "Run scripts/setup_benchmark_env_mac_linux.sh first."
  exit 1
fi
if ! .venv-benchmark/bin/python scripts/benchmark.py status --require-ready; then
  echo "The prospective holdout remains sealed until at least 3 November 2026."
  exit 0
fi

if [ ! -f vendor/Kronos/model/__init__.py ]; then
  MARKETFORGE_PYTHON=.venv-benchmark/bin/python MARKETFORGE_SKIP_KRONOS_DEPS=1 ./scripts/install_kronos_mac_linux.sh
fi

.venv-benchmark/bin/python scripts/benchmark.py freeze-data
.venv-benchmark/bin/python scripts/benchmark.py verify-models --download-weights
.venv-benchmark/bin/python scripts/benchmark.py verify-environment
.venv-benchmark/bin/python scripts/benchmark.py lock-protocol
.venv-benchmark/bin/python scripts/benchmark.py run --models marketforge-naive,marketforge-ensemble,marketforge-regime-ensemble,kronos-base
.venv-benchmark/bin/python scripts/benchmark.py verify-results --models marketforge-naive,marketforge-ensemble,marketforge-regime-ensemble,kronos-base
.venv-benchmark/bin/python scripts/benchmark.py report --candidate marketforge-regime-ensemble --comparator kronos-base

echo "Finished. Open benchmarks/frozen_v3/results/benchmark_report.md"
