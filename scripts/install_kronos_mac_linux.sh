#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."

if ! command -v git >/dev/null 2>&1; then
  echo "Git is required. Install Git, then run this script again."
  exit 1
fi
PYTHON_BIN="${MARKETFORGE_PYTHON:-.venv/bin/python}"
if [ ! -x "$PYTHON_BIN" ]; then
  echo "Python environment not found at $PYTHON_BIN."
  exit 1
fi

KRONOS_REF="${KRONOS_REF:-d5ffd46ab061af1146ea415e4ce86d24b5231b01}"
if [ ! -d vendor/Kronos ]; then
  git clone --filter=blob:none https://github.com/shiyu-coder/Kronos.git vendor/Kronos
  git -C vendor/Kronos checkout "$KRONOS_REF"
else
  if [ ! -d vendor/Kronos/.git ]; then
    echo "vendor/Kronos exists but is not a Git checkout. Move it away and try again."
    exit 1
  fi
  ACTUAL_REF="$(git -C vendor/Kronos rev-parse HEAD)"
  if [ "$ACTUAL_REF" != "$KRONOS_REF" ]; then
    echo "Existing Kronos commit $ACTUAL_REF does not match pinned commit $KRONOS_REF."
    echo "For safety, MarketForge will not modify or replace it automatically."
    exit 1
  fi
  echo "Existing Kronos checkout matches the pinned commit."
fi

if [ "${MARKETFORGE_SKIP_KRONOS_DEPS:-0}" != "1" ]; then
  "$PYTHON_BIN" -m pip install -r requirements-kronos.txt
fi
"$PYTHON_BIN" scripts/patch_kronos_compat.py vendor/Kronos
git -C vendor/Kronos rev-parse HEAD > vendor/Kronos/.marketforge-source-commit.txt

echo "Kronos is installed and its compatibility patch was recorded. Restart MarketForge AI."
