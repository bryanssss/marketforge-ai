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


def benchmark_source_paths(project_root: Path) -> list[Path]:
    """Return every source/dependency file that can alter frozen benchmark output."""
    paths = [*project_root.glob("app/**/*.py")]
    for relative in (
        "scripts/benchmark.py",
        "scripts/patch_kronos_compat.py",
        "pyproject.toml",
        "requirements.txt",
        "requirements-kronos.txt",
        "requirements-benchmark.txt",
    ):
        paths.append(project_root / relative)
    return sorted({path for path in paths if path.is_file()})


def code_tree_sha256(project_root: Path) -> str:
    digest = hashlib.sha256()
    for path in benchmark_source_paths(project_root):
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
        required = {"benchmark_id", "version", "frozen_at", "data", "execution", "evaluation", "statistics", "claim_gate"}
        missing = sorted(required - self.raw.keys())
        if missing:
            raise BenchmarkSpecError("Missing benchmark fields: " + ", ".join(missing))
        data, execution, evaluation = self.raw["data"], self.raw["execution"], self.raw["evaluation"]
        if data.get("provider") != "binance-public-data":
            raise BenchmarkSpecError("The prospective benchmark requires the official Binance public-data provider.")
        start = datetime.fromisoformat(data["context_start"].replace("Z", "+00:00"))
        holdout = datetime.fromisoformat(data["holdout_start"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(data["holdout_end_exclusive"].replace("Z", "+00:00"))
        frozen_at = datetime.fromisoformat(self.raw["frozen_at"].replace("Z", "+00:00"))
        available_at = datetime.fromisoformat(data["data_available_not_before"].replace("Z", "+00:00"))
        if any(value.tzinfo is None for value in (start, holdout, end, frozen_at, available_at)):
            raise BenchmarkSpecError("Benchmark dates must include a timezone.")
        if not (frozen_at < holdout and start < holdout < end <= available_at):
            raise BenchmarkSpecError("Expected frozen_at < holdout_start and context_start < holdout_start < holdout_end <= availability.")
        symbols = list(data.get("symbols", [])); horizons = [int(v) for v in evaluation.get("horizons", [])]
        seeds = [int(v) for v in evaluation.get("seeds", [])]; models = list(evaluation.get("models", []))
        if not symbols or not horizons or not seeds:
            raise BenchmarkSpecError("Symbols, horizons and seeds cannot be empty.")
        if len(symbols) != len(set(symbols)) or len(horizons) != len(set(horizons)) or len(seeds) != len(set(seeds)):
            raise BenchmarkSpecError("Symbols, horizons and seeds must be unique.")
        if any(value < 1 for value in horizons) or int(evaluation["lookback"]) < 40:
            raise BenchmarkSpecError("Invalid forecast horizon or lookback.")
        origin_hour = int(evaluation.get("origin_hour_utc", -1))
        if origin_hour < 0 or origin_hour > 23 or int(evaluation.get("origin_frequency_hours", 0)) < 1:
            raise BenchmarkSpecError("An explicit UTC origin hour and positive origin frequency are required.")
        if execution.get("device") != "cpu" or execution.get("deterministic_algorithms") is not True:
            raise BenchmarkSpecError("Frozen v2 requires deterministic CPU execution.")
        if int(execution.get("thread_count", 0)) != 1:
            raise BenchmarkSpecError("Frozen v2 requires a single numerical thread.")
        if not execution.get("python_major_minor") or not execution.get("required_packages"):
            raise BenchmarkSpecError("Execution environment versions must be frozen.")
        if not models or evaluation.get("candidate") not in models:
            raise BenchmarkSpecError("The candidate must appear in the frozen model list.")
        for key in ("primary_comparator", "sanity_comparator"):
            if evaluation.get(key) not in models:
                raise BenchmarkSpecError(f"{key} must appear in the frozen model list.")


def load_spec(path: Path) -> FrozenSpec:
    spec = FrozenSpec(path=path, raw=read_json(path)); spec.validate(); return spec


def make_preregistration_lock(spec: FrozenSpec, model_lock: dict[str, Any], *, code_sha256: str, git_commit: str | None, git_dirty: bool | None) -> dict[str, Any]:
    payload = {"benchmark_id": spec.benchmark_id, "frozen_at": spec.raw["frozen_at"], "created_at": datetime.now(timezone.utc).isoformat(), "spec_sha256": spec.hash, "model_lock_sha256": sha256_json(model_lock), "code_sha256": code_sha256, "git_commit": git_commit, "git_dirty": git_dirty, "status": "preregistered", "rule": "Changing a bound hash requires a new benchmark identifier; this lock must not be overwritten."}
    payload["preregistration_sha256"] = sha256_json(payload); return payload


def verify_preregistration(preregistration: dict[str, Any], spec: FrozenSpec, model_lock: dict[str, Any], code_sha256: str) -> list[str]:
    problems: list[str] = []
    checks = ((preregistration.get("status") == "preregistered", "Preregistration status is not preregistered."), (preregistration.get("benchmark_id") == spec.benchmark_id, "Benchmark identifier does not match."), (preregistration.get("spec_sha256") == spec.hash, "Specification changed after preregistration."), (preregistration.get("model_lock_sha256") == sha256_json(model_lock), "Model lock changed after preregistration."), (preregistration.get("code_sha256") == code_sha256, "Benchmark-relevant code changed after preregistration."))
    problems.extend(message for ok, message in checks if not ok)
    payload = dict(preregistration); expected = payload.pop("preregistration_sha256", None)
    if expected != sha256_json(payload): problems.append("Preregistration lock integrity hash is invalid.")
    return problems


def make_protocol_lock(spec: FrozenSpec, model_lock: dict[str, Any], data_lock: dict[str, Any], git_commit: str | None, git_dirty: bool | None, code_sha256: str | None = None, model_verification: dict[str, Any] | None = None, environment_verification: dict[str, Any] | None = None, preregistration: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {"benchmark_id": spec.benchmark_id, "created_at": datetime.now(timezone.utc).isoformat(), "spec_sha256": spec.hash, "model_lock_sha256": sha256_json(model_lock), "data_lock_sha256": sha256_json(data_lock), "git_commit": git_commit, "git_dirty": git_dirty, "code_sha256": code_sha256, "model_verification_sha256": sha256_json(model_verification) if model_verification else None, "environment_verification_sha256": sha256_json(environment_verification) if environment_verification else None, "preregistration_sha256": preregistration.get("preregistration_sha256") if preregistration else None, "status": "incomplete"}
    if data_lock.get("status") == "verified" and code_sha256 and model_verification and model_verification.get("all_verified") and environment_verification and environment_verification.get("all_verified") and preregistration and preregistration.get("status") == "preregistered": payload["status"] = "frozen"
    payload["protocol_sha256"] = sha256_json(payload); return payload
