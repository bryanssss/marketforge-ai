from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PATCH_ID = "marketforge-preserve-kronos-amount-v1"


def patch_text(source: str) -> tuple[str, int]:
    """Remove the upstream unconditional amount reset while preserving safe defaults."""
    lines = source.splitlines(keepends=True)
    output: list[str] = []
    patched = 0
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if stripped.startswith("df[self.amt_vol] = 0.0") and index + 1 < len(lines):
            next_line = lines[index + 1]
            if "if self.amt_vol not in df.columns and self.vol_col in df.columns:" in next_line:
                indent = next_line[: len(next_line) - len(next_line.lstrip())]
                output.append(f"{indent}if self.amt_vol not in df.columns:\n")
                patched += 1
                index += 2
                continue
        output.append(line)
        index += 1
    return "".join(output), patched


def git_commit(repo: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def apply_patch(kronos_dir: Path) -> dict[str, object]:
    target = kronos_dir / "model" / "kronos.py"
    licence = kronos_dir / "LICENSE"
    if not target.exists() or not licence.exists():
        raise RuntimeError("Kronos source or its LICENSE file is missing; refusing to patch.")

    source = target.read_text(encoding="utf-8")
    patched_source, count = patch_text(source)
    marker = kronos_dir / ".marketforge-patches.json"
    if count == 0:
        if marker.exists() and PATCH_ID in marker.read_text(encoding="utf-8"):
            return {"status": "already-patched", "patch_id": PATCH_ID, "changes": 0}
        raise RuntimeError(
            "The expected Kronos amount-handling pattern was not found. The upstream code may have changed; "
            "no file was modified."
        )

    backup_dir = kronos_dir / ".marketforge-backups"
    backup_dir.mkdir(exist_ok=True)
    backup = backup_dir / "kronos.py.original"
    if not backup.exists():
        shutil.copy2(target, backup)

    target.write_text(patched_source, encoding="utf-8")
    record = {
        "patch_id": PATCH_ID,
        "applied_at_utc": datetime.now(timezone.utc).isoformat(),
        "upstream_commit": git_commit(kronos_dir),
        "file": "model/kronos.py",
        "changes": count,
        "reason": "Preserve a supplied amount column and infer it only when absent.",
        "backup": ".marketforge-backups/kronos.py.original",
        "original_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "patched_sha256": hashlib.sha256(patched_source.encode("utf-8")).hexdigest(),
    }
    marker.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return {"status": "patched", **record}


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply verified MarketForge compatibility fixes to Kronos.")
    parser.add_argument("kronos_dir", nargs="?", default="vendor/Kronos")
    args = parser.parse_args()
    try:
        result = apply_patch(Path(args.kronos_dir).resolve())
    except RuntimeError as exc:
        print(f"Patch not applied: {exc}")
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
