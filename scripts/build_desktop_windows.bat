@echo off
setlocal
cd /d "%~dp0\.."
if not exist .venv-desktop py -3.11 -m venv .venv-desktop
call .venv-desktop\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements-desktop.txt
pyinstaller --clean marketforge-desktop.spec
echo.
echo Desktop build created in dist\MarketForgeAI.exe
pause
