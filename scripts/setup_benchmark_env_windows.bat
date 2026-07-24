@echo off
setlocal
cd /d "%~dp0\.."
py -3.11 -m venv .venv-benchmark
if errorlevel 1 (
  echo Python 3.11 is required. Install it, then run this file again.
  pause
  exit /b 1
)
.venv-benchmark\Scripts\python.exe -m pip install --upgrade pip
.venv-benchmark\Scripts\python.exe -m pip install -r requirements-benchmark.txt
if errorlevel 1 (
  echo The benchmark packages could not be installed.
  pause
  exit /b 1
)
echo Dedicated frozen benchmark environment created.
pause
