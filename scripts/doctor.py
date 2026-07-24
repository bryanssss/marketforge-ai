from __future__ import annotations

import importlib.metadata
import json
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ("fastapi", "uvicorn", "python-multipart", "pandas", "numpy", "pydantic")


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

    sample = ROOT / "data" / "sample_market_data.csv"
    checks.append({"check": "sample_data", "ok": sample.exists(), "value": str(sample)})
    kronos = ROOT / "vendor" / "Kronos"
    checks.append(
        {
            "check": "kronos_optional",
            "ok": (kronos / "model" / "__init__.py").exists(),
            "value": "installed" if kronos.exists() else "not installed",
            "required": False,
        }
    )
    payload = {"marketforge_root": str(ROOT), "checks": checks}
    print(json.dumps(payload, indent=2))
    required_failures = [
        check for check in checks if check.get("required", True) is not False and not check["ok"]
    ]
    return 1 if required_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
