from __future__ import annotations

import importlib.metadata
import json
import platform
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ("fastapi", "uvicorn", "python-multipart", "pandas", "numpy", "pydantic")


def _check_storage() -> dict[str, object]:
    storage = ROOT / "storage"
    try:
        storage.mkdir(parents=True, exist_ok=True)
        probe = storage / ".doctor-write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        with sqlite3.connect(":memory:") as connection:
            connection.execute("SELECT 1").fetchone()
        return {"check": "local_storage", "ok": True, "value": str(storage)}
    except OSError as exc:
        return {"check": "local_storage", "ok": False, "value": str(exc)}


def main() -> int:
    checks: list[dict[str, object]] = []
    version_ok = (3, 10) <= sys.version_info[:2] < (3, 14)
    checks.append(
        {
            "check": "python",
            "ok": version_ok,
            "value": platform.python_version(),
            "required": ">=3.10,<3.14",
        }
    )
    for package in REQUIRED:
        try:
            version = importlib.metadata.version(package)
            checks.append({"check": f"package:{package}", "ok": True, "value": version})
        except importlib.metadata.PackageNotFoundError:
            checks.append({"check": f"package:{package}", "ok": False, "value": "missing"})

    required_files = (
        "data/sample_market_data.csv",
        "app/static/index.html",
        "app/static/app.js",
        "benchmarks/frozen_v3/spec.json",
        "benchmarks/frozen_v3/model_lock.json",
        "benchmarks/frozen_v3/preregistration_lock.json",
    )
    for relative in required_files:
        path = ROOT / relative
        checks.append({"check": f"file:{relative}", "ok": path.is_file(), "value": str(path)})

    checks.append(_check_storage())

    kronos = ROOT / "vendor" / "Kronos"
    checks.append(
        {
            "check": "kronos_optional",
            "ok": (kronos / "model" / "__init__.py").exists(),
            "value": "installed" if kronos.exists() else "not installed",
            "required": False,
        }
    )
    desktop_available = False
    try:
        importlib.metadata.version("pywebview")
        desktop_available = True
    except importlib.metadata.PackageNotFoundError:
        pass
    checks.append(
        {
            "check": "desktop_optional",
            "ok": desktop_available,
            "value": "dependencies installed" if desktop_available else "not installed",
            "required": False,
        }
    )

    payload = {
        "project": "MarketForge AI",
        "version": "0.5.0",
        "marketforge_root": str(ROOT),
        "checks": checks,
    }
    print(json.dumps(payload, indent=2))
    required_failures = [
        check for check in checks if check.get("required", True) is not False and not check["ok"]
    ]
    return 1 if required_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
