@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
  set PYTHON=py -3
) else (
  set PYTHON=python
)

if not exist .venv (
  echo Creating MarketForge's private Python environment...
  %PYTHON% -m venv .venv
  if errorlevel 1 goto :python_error
)

.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto :install_error

.venv\Scripts\python.exe scripts\doctor.py
if errorlevel 1 goto :doctor_error

start "" http://127.0.0.1:7070
.venv\Scripts\python.exe run.py
goto :end

:python_error
echo.
echo Python 3.10 to 3.13 was not found.
echo Install Python and tick "Add Python to PATH" during installation.
pause
goto :end

:install_error
echo.
echo The Python packages could not be installed. Check your internet connection.
pause
goto :end

:doctor_error
echo.
echo MarketForge's self-check found a missing requirement. Read the report above.
pause

:end
endlocal
