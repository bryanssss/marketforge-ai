#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3.11 -m venv .venv-desktop
source .venv-desktop/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-desktop.txt
pyinstaller --clean marketforge-desktop.spec
echo "Desktop build created in dist/MarketForgeAI"
