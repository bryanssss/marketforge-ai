from __future__ import annotations

import importlib.metadata
import os
import platform
from datetime import datetime, timezone
from typing import Any

from app.benchmark.spec import FrozenSpec, sha256_json

_THREAD_VARS = (
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)


def _package_versions() -> dict[str, str]:
    """Capture the complete installed distribution set in a stable form."""
    packages: dict[str, str] = {}
    for distribution in importlib.metadata.distributions():
        name = distribution.metadata.get("Name")
        if name:
            packages[name.lower().replace("_", "-")] = distribution.version
    return dict(sorted(packages.items()))


def environment_fingerprint(spec: FrozenSpec) -> dict[str, Any]:
    """Build a stable fingerprint of the environment that will execute forecasts."""
    expected = spec.raw["execution"]
    required = {
        name: _package_versions().get(name.lower().replace("_", "-"))
        for name in expected["required_packages"]
    }
    torch_info: dict[str, Any] = {"available": False}
    try:
        import torch

        thread_count = int(expected["thread_count"])
        torch.set_num_threads(thread_count)
        try:
            torch.set_num_interop_threads(thread_count)
        except RuntimeError:
            # PyTorch only permits setting this before inter-op work starts. We still
            # record and verify the active value below.
            pass
        torch_info = {
            "available": True,
            "version": torch.__version__.split("+")[0],
            "num_threads": torch.get_num_threads(),
            "num_interop_threads": torch.get_num_interop_threads(),
            "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
            "cuda_available": torch.cuda.is_available(),
            "mps_available": bool(
                getattr(torch.backends, "mps", None)
                and torch.backends.mps.is_available()
            ),
        }
    except Exception:
        pass
    return {
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "required_packages": required,
        "all_packages": _package_versions(),
        "thread_environment": {name: os.getenv(name) for name in _THREAD_VARS},
        "torch": torch_info,
    }


def capture_environment(spec: FrozenSpec) -> dict[str, Any]:
    fingerprint = environment_fingerprint(spec)
    payload: dict[str, Any] = {
        "benchmark_id": spec.benchmark_id,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "fingerprint": fingerprint,
        "fingerprint_sha256": sha256_json(fingerprint),
    }
    payload["environment_sha256"] = sha256_json(payload)
    return payload


def verify_environment(
    record: dict[str, Any],
    spec: FrozenSpec,
    *,
    compare_current: bool = True,
) -> list[str]:
    problems: list[str] = []
    payload = dict(record)
    expected_hash = payload.pop("environment_sha256", None)
    payload.pop("all_verified", None)
    payload.pop("problems", None)
    if expected_hash != sha256_json(payload):
        problems.append("Environment record integrity hash is invalid.")

    fingerprint = record.get("fingerprint")
    if not isinstance(fingerprint, dict):
        return problems + ["Environment fingerprint is missing."]
    if record.get("fingerprint_sha256") != sha256_json(fingerprint):
        problems.append("Environment fingerprint hash is invalid.")

    expected = spec.raw["execution"]
    if ".".join(str(fingerprint.get("python", "")).split(".")[:2]) != str(
        expected["python_major_minor"]
    ):
        problems.append("Python major/minor version does not match the frozen profile.")
    for name, version in expected["required_packages"].items():
        if fingerprint.get("required_packages", {}).get(name) != version:
            problems.append(f"Package {name} does not match frozen version {version}.")
    torch_info = fingerprint.get("torch", {})
    if expected.get("device") == "cpu" and torch_info.get("available"):
        if torch_info.get("num_threads") != int(expected["thread_count"]):
            problems.append("PyTorch numerical thread count does not match.")
        if torch_info.get("num_interop_threads") != int(expected["thread_count"]):
            problems.append("PyTorch inter-op thread count does not match.")
    for name, value in fingerprint.get("thread_environment", {}).items():
        if value != str(expected["thread_count"]):
            problems.append(f"{name} is not set to the frozen thread count.")

    if compare_current and not problems:
        current = environment_fingerprint(spec)
        if sha256_json(current) != record.get("fingerprint_sha256"):
            problems.append(
                "The live execution environment changed after the environment lock was created."
            )
    return problems


def build_environment_verification(spec: FrozenSpec) -> dict[str, Any]:
    record = capture_environment(spec)
    problems = verify_environment(record, spec, compare_current=True)
    record["all_verified"] = not problems
    record["problems"] = problems
    return record
