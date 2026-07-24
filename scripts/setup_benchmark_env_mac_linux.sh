#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
if ! command -v python3.11 >/dev/null 2>&1; then
  echo "Python 3.11 is required for the frozen benchmark."
  exit 1
fi
python3.11 -m venv .venv-benchmark
.venv-benchmark/bin/python -m pip install --upgrade pip
.venv-benchmark/bin/python -m pip install -r requirements-benchmark.txt
echo "Dedicated frozen benchmark environment created."
