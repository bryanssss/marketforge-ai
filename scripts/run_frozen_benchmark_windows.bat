@echo off
setlocal
set OMP_NUM_THREADS=1
set MKL_NUM_THREADS=1
set OPENBLAS_NUM_THREADS=1
set NUMEXPR_NUM_THREADS=1
cd /d "%~dp0\.."

if not exist .venv-benchmark\Scripts\python.exe (
  echo Run scripts\setup_benchmark_env_windows.bat first.
  pause
  exit /b 1
)
.venv-benchmark\Scripts\python.exe scripts\benchmark.py status --require-ready
if errorlevel 1 (
  echo.
  echo The prospective holdout is still sealed. The full data may be collected on or after 3 November 2026.
  echo This is intentional: the scored candles must not exist when the benchmark is designed.
  pause
  exit /b 0
)

if not exist vendor\Kronos\model\__init__.py (
  echo Installing the pinned Kronos source first...
  set MARKETFORGE_PYTHON=.venv-benchmark\Scripts\python.exe
  set MARKETFORGE_SKIP_KRONOS_DEPS=1
  call scripts\install_kronos_windows.bat
  if errorlevel 1 exit /b 1
)

echo Step 1 of 7: Downloading and verifying official frozen data...
.venv-benchmark\Scripts\python.exe scripts\benchmark.py freeze-data
if errorlevel 1 goto :failed

echo Step 2 of 7: Downloading and verifying pinned model weights...
.venv-benchmark\Scripts\python.exe scripts\benchmark.py verify-models --download-weights
if errorlevel 1 goto :failed

echo Step 3 of 7: Verifying the exact execution environment...
.venv-benchmark\Scripts\python.exe scripts\benchmark.py verify-environment
if errorlevel 1 goto :failed

echo Step 4 of 7: Freezing the protocol lock...
.venv-benchmark\Scripts\python.exe scripts\benchmark.py lock-protocol
if errorlevel 1 goto :failed

echo Step 5 of 7: Running or resuming matched forecasts...
.venv-benchmark\Scripts\python.exe scripts\benchmark.py run --models marketforge-naive,marketforge-ensemble,kronos-base
if errorlevel 1 goto :failed

echo Step 6 of 7: Replaying every forecast for deterministic verification...
.venv-benchmark\Scripts\python.exe scripts\benchmark.py verify-results --models marketforge-naive,marketforge-ensemble,kronos-base
if errorlevel 1 goto :failed

echo Step 7 of 7: Building the statistical report...
.venv-benchmark\Scripts\python.exe scripts\benchmark.py report --candidate marketforge-ensemble --comparator kronos-base
if errorlevel 1 goto :failed

echo.
echo Finished. Open benchmarks\frozen_v2\results\benchmark_report.md
pause
exit /b 0

:failed
echo.
echo The benchmark stopped safely. Read the error above. Running this file again resumes completed predictions.
pause
exit /b 1
