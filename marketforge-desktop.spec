# Build with: pyinstaller marketforge-desktop.spec
from PyInstaller.utils.hooks import collect_submodules

datas = [
    ("app/static", "app/static"),
    ("data/sample_market_data.csv", "data"),
]
hiddenimports = collect_submodules("uvicorn") + collect_submodules("webview")

a = Analysis(
    ["desktop.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="MarketForgeAI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
