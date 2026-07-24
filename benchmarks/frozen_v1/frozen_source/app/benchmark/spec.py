from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class BenchmarkSpecError(ValueError):
    """Raised when a benchmark specification is incomplete or inconsistent."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()



def code_tree_sha256(project_root: Path) -> str:
    """Hash benchmark-relevant source files in a path-stable order."""
    digest = hashlib.sha256()
    paths = sorted([*project_root.glob("app/**/*.py"), project_root / "scripts" / "benchmark.py", project_root / "pyproject.toml"])
    for path in paths:
        if not path.is_file():
            continue
        relative = path.relative_to(project_root).as_posix().encode("utf-8")
        content = path.read_bytes()
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BenchmarkSpecError(f"Could not read valid JSON from {path}.") from exc
    if not isinstance(value, dict):
        raise BenchmarkSpecError(f"{path} must contain a JSON object.")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


@dataclass(frozen=True)
class FrozenSpec:
    path: Path
    raw: dict[str, Any]

    @property
    def hash(self) -> str:
        return sha256_json(self.raw)

    @property
    def benchmark_id(self) -> str:
        return str(self.raw["benchmark_id"])

    @property
    def assets(self) -> list[str]:
        return list(self.raw["data"]["symbols"])

    @property
    def horizons(self) -> list[int]:
        return [int(value) for value in self.raw["evaluation"]["horizons"]]

    def validate(self) -> None:
        required = {"benchmark_id", "version", "frozen_at", "data", "evaluation", "statistics", "claim_gate"}
        missing = sorted(required - self.raw.keys())
        if missing:
            raise BenchmarkSpecError("Missing benchmark fields: " + ", ".join(missing))
        data = self.raw["data"]
        evaluation = self.raw["evaluation"]
        if data.get("provider") != "binance-public-data":
            raise BenchmarkSpecError("Frozen v1 requires the official Binance public-data provider.")
        if not data.get("symbols") or not evaluation.get("horizons"):
            raise BenchmarkSpecError("At least one symbol and one horizon are required.")
        start = datetime.fromisoformat(data["context_start"].replace("Z", "+00:00"))
        holdout = datetime.fromisoformat(data["holdout_start"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(data["holdout_end_exclusive"].replace("Z", "+00:00"))
        frozen_at = datetime.fromisoformat(self.raw["frozen_at"].replace("Z", "+00:00"))
        available_at = datetime.fromisoformat(
            data["data_available_not_before"].replace("Z", "+00:00")
        )
        dates = (start, holdout, end, frozen_at, available_at)
        if any(value.tzinfo is None for value in dates):
            raise BenchmarkSpecError("Benchmark dates must include a timezone.")
        if not (frozen_at < holdout and start < holdout < end <= available_at):
            raise BenchmarkSpecError(
                "Expected frozen_at < holdout_start, context_start < holdout_start < "
                "holdout_end_exclusive <= data_available_not_before."
            )
        symbols = list(data["symbols"])
        horizons = [int(value) for value in evaluation["horizons"]]
        seeds = [int(value) for value in evaluation["seeds"]]
        models = list(evaluation["models"])
        if len(symbols) != len(set(symbols)) or len(horizons) != len(set(horizons)):
            raise BenchmarkSpecError("Symbols and horizons must be unique.")
        if len(seeds) != len(set(seeds)) or not seeds:
            raise BenchmarkSpecError("At least one unique seed is required.")
        if any(value < 1 for value in horizons):
            raise BenchmarkSpecError("Forecast horizons must be positive integers.")
        if int(evaluation["lookback"]) < 40 or int(evaluation["origin_step"]) < 1:
            raise BenchmarkSpecError("Invalid lookback or origin step.")
        if not models or evaluation.get("candidate") not in models:
            raise BenchmarkSpecError("The candidate must appear in the frozen model list.")
        for key in ("primary_comparator", "sanity_comparator"):
            if evaluation.get(key) not in models:
                raise BenchmarkSpecError(f"{key} must appear in the frozen model list.")


def load_spec(path: Path) -> FrozenSpec:
    spec = FrozenSpec(path=path, raw=read_json(path))
    spec.validate()
    return spec



def make_preregistration_lock(
    spec: FrozenSpec,
    model_lock: dict[str, Any],
    *,
    code_sha256: str,
    git_commit: str | None,
    git_dirty: bool | None,
) -> dict[str, Any]:
    payload = {
        "benchmark_id": spec.benchmark_id,
        "frozen_at": spec.raw["frozen_at"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "spec_sha256": spec.hash,
        "model_lock_sha256": sha256_json(model_lock),
        "code_sha256": code_sha256,
        "git_commit": git_commit,
        "git_dirty": git_dirty,
        "status": "preregistered",
        "rule": "Changing a bound hash requires a new benchmark identifier; this lock must not be overwritten.",
    }
    payload["preregistration_sha256"] = sha256_json(payload)
    return payload


def verify_preregistration(
    preregistration: dict[str, Any],
    spec: FrozenSpec,
    model_lock: dict[str, Any],
    code_sha256: str,
) -> list[str]:
    problems: list[str] = []
    if preregistration.get("status") != "preregistered":
        problems.append("Preregistration status is not preregistered.")
    if preregistration.get("benchmark_id") != spec.benchmark_id:
        problems.append("Benchmark identifier does not match the preregistration.")
    if preregistration.get("spec_sha256") != spec.hash:
        problems.append("Specification changed after preregistration.")
    if preregistration.get("model_lock_sha256") != sha256_json(model_lock):
        problems.append("Model lock changed after preregistration.")
    if preregistration.get("code_sha256") != code_sha256:
        problems.append("Benchmark-relevant code changed after preregistration.")
    expected_hash = preregistration.get("preregistration_sha256")
    payload = dict(preregistration)
    payload.pop("preregistration_sha256", None)
    if expected_hash != sha256_json(payload):
        problems.append("Preregistration lock integrity hash is invalid.")
    return problems


def make_protocol_lock(
    spec: FrozenSpec,
    model_lock: dict[str, Any],
    data_lock: dict[str, Any],
    git_commit: str | None,
    git_dirty: bool | None,
    code_sha256: str | None = None,
    model_verification: dict[str, Any] | None = None,
    preregistration: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "benchmark_id": spec.benchmark_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "spec_sha256": spec.hash,
        "model_lock_sha256": sha256_json(model_lock),
        "data_lock_sha256": sha256_json(data_lock),
        "git_commit": git_commit,
        "git_dirty": git_dirty,
        "code_sha256": code_sha256,
        "model_verification_sha256": sha256_json(model_verification) if model_verification else None,
        "preregistration_sha256": preregistration.get("preregistration_sha256") if preregistration else None,
        "status": (
            "frozen"
            if data_lock.get("status") == "verified"
            and bool(code_sha256)
            and bool(model_verification and model_verification.get("all_verified"))
            and bool(preregistration and preregistration.get("status") == "preregistered")
            else "incomplete"
        ),
    }
    payload["protocol_sha256"] = sha256_json(payload)
    return payload
