from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "RELEASE_MANIFEST.json"
EXCLUDED_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
EXCLUDED_FILES = {".coverage", OUTPUT.name}


def main() -> int:
    files: list[dict[str, object]] = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        if relative.name in EXCLUDED_FILES or relative.parts[:2] == ("vendor", "Kronos"):
            continue
        content = path.read_bytes()
        files.append(
            {
                "path": relative.as_posix(),
                "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    payload = {
        "project": "MarketForge AI",
        "version": "0.5.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "file_count": len(files),
        "files": files,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT} with {len(files)} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
