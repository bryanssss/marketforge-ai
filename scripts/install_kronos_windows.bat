@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0\.."

where git >nul 2>nul
if errorlevel 1 (
  echo Git is not installed. Install GitHub Desktop or Git for Windows, then try again.
  pause
  exit /b 1
)
if "%MARKETFORGE_PYTHON%"=="" set MARKETFORGE_PYTHON=.venv\Scripts\python.exe
if not exist "%MARKETFORGE_PYTHON%" (
  echo Python environment not found at %MARKETFORGE_PYTHON%.
  pause
  exit /b 1
)

if "%KRONOS_REF%"=="" set KRONOS_REF=d5ffd46ab061af1146ea415e4ce86d24b5231b01
if exist vendor\Kronos (
  if not exist vendor\Kronos\.git (
    echo vendor\Kronos exists but is not a Git checkout. Move it away and try again.
    pause
    exit /b 1
  )
  for /f %%i in ('git -C vendor\Kronos rev-parse HEAD') do set ACTUAL_REF=%%i
  if /I not "!ACTUAL_REF!"=="%KRONOS_REF%" (
    echo Existing Kronos commit !ACTUAL_REF! does not match pinned commit %KRONOS_REF%.
    echo For safety, MarketForge will not modify or replace it automatically.
    pause
    exit /b 1
  )
  echo Existing Kronos checkout matches the pinned commit.
) else (
  echo Downloading official Kronos source...
  git clone --filter=blob:none https://github.com/shiyu-coder/Kronos.git vendor\Kronos
  if errorlevel 1 goto :clone_error
  git -C vendor\Kronos checkout "%KRONOS_REF%"
  if errorlevel 1 goto :clone_error
)

if not "%MARKETFORGE_SKIP_KRONOS_DEPS%"=="1" (
  "%MARKETFORGE_PYTHON%" -m pip install -r requirements-kronos.txt
  if errorlevel 1 goto :install_error
)

"%MARKETFORGE_PYTHON%" scripts\patch_kronos_compat.py vendor\Kronos
if errorlevel 1 goto :patch_error

git -C vendor\Kronos rev-parse HEAD > vendor\Kronos\.marketforge-source-commit.txt

echo.
echo Kronos is installed and its compatibility patch was recorded.
echo Restart MarketForge AI, then check the engine status at the top of the page.
pause
exit /b 0

:clone_error
echo.
echo Kronos could not be downloaded. Check your internet connection and KRONOS_REF value.
pause
exit /b 1

:install_error
echo.
echo Kronos dependencies could not be installed.
pause
exit /b 1

:patch_error
echo.
echo Kronos was downloaded, but the safe compatibility patch could not be verified.
echo Nothing was silently changed. See the message above and open a GitHub issue.
pause
exit /b 1
