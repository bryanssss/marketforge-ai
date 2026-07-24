#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.benchmark.data import freeze_data, sha256_file, verify_data_lock
from app.benchmark.environment import build_environment_verification, verify_environment
from app.benchmark.report import build_report, save_report
from app.benchmark.runner import compare_replay_ledgers, run_benchmark, verify_prediction_ledger
from app.benchmark.spec import (
    code_tree_sha256,
    load_spec,
    make_preregistration_lock,
    make_protocol_lock,
    read_json,
    verify_preregistration,
    write_json,
)

DEFAULT_ROOT = PROJECT_ROOT / "benchmarks" / "frozen_v3"


def git_state() -> tuple[str | None, bool | None]:
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, text=True, stderr=subprocess.DEVNULL).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=PROJECT_ROOT, text=True).strip())
        return commit, dirty
    except (OSError, subprocess.CalledProcessError):
        return None, None


def verify_models(root: Path, spec, download_weights: bool) -> dict:
    from datetime import datetime, timezone

    lock = read_json(root / "model_lock.json")
    results: list[dict[str, object]] = []
    source_commit = lock["kronos_source"]["commit"]
    vendor = PROJECT_ROOT / "vendor" / "Kronos"
    installed_commit = None
    source_status = "not-installed"
    if (vendor / ".git").exists():
        installed_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=vendor, text=True
        ).strip()
        source_status = "verified" if installed_commit == source_commit else "mismatch"
    results.append(
        {
            "kind": "source",
            "expected": source_commit,
            "actual": installed_commit,
            "status": source_status,
        }
    )

    patch_marker = vendor / ".marketforge-patches.json"
    patch_id = lock["kronos_source"].get("compatibility_patch")
    patch_actual = None
    patch_status = "missing"
    patched_file_sha = None
    marker: dict[str, object] = {}
    if patch_marker.exists():
        try:
            marker = json.loads(patch_marker.read_text(encoding="utf-8"))
            patch_actual = marker.get("patch_id")
            target = vendor / str(marker.get("file", "model/kronos.py"))
            if target.exists():
                patched_file_sha = sha256_file(target)
            patch_status = (
                "verified"
                if patch_actual == patch_id
                and marker.get("upstream_commit") == source_commit
                and marker.get("patched_sha256") == patched_file_sha
                else "mismatch"
            )
        except (json.JSONDecodeError, OSError):
            patch_status = "invalid"
    results.append(
        {
            "kind": "compatibility-patch",
            "expected": patch_id,
            "actual": patch_actual,
            "patched_file_sha256": patched_file_sha,
            "status": patch_status,
        }
    )

    required_models = [
        name for name in spec.raw["evaluation"]["models"] if name.startswith("kronos-")
    ]
    required_tokenizers = sorted(
        {lock["models"][name]["tokenizer"] for name in required_models}
    )
    cache = root / "model_cache"
    snapshot_download = None
    if download_weights:
        try:
            from huggingface_hub import snapshot_download as hf_snapshot_download
        except ImportError as exc:
            raise SystemExit(
                "Install optional Kronos dependencies first; huggingface_hub is required."
            ) from exc
        snapshot_download = hf_snapshot_download

    for model_name in required_models:
        item = lock["models"][model_name]
        if snapshot_download is None:
            results.append(
                {
                    "kind": "model",
                    "name": model_name,
                    "revision": item["revision"],
                    "status": "not-checked",
                }
            )
            continue
        folder = Path(
            snapshot_download(
                repo_id=item["repo_id"],
                revision=item["revision"],
                allow_patterns=["config.json", "model.safetensors"],
                local_dir=cache / model_name,
            )
        )
        weight = folder / "model.safetensors"
        actual = sha256_file(weight)
        status = "verified" if actual == item["model_safetensors_sha256"] else "mismatch"
        results.append(
            {
                "kind": "model",
                "name": model_name,
                "revision": item["revision"],
                "expected": item["model_safetensors_sha256"],
                "actual": actual,
                "status": status,
            }
        )

    for token_name in required_tokenizers:
        item = lock["tokenizers"][token_name]
        if snapshot_download is None:
            results.append(
                {
                    "kind": "tokenizer",
                    "name": token_name,
                    "revision": item["revision"],
                    "status": "not-checked",
                }
            )
            continue
        folder = Path(
            snapshot_download(
                repo_id=item["repo_id"],
                revision=item["revision"],
                allow_patterns=["config.json", "model.safetensors"],
                local_dir=cache / token_name,
            )
        )
        weight = folder / "model.safetensors"
        actual = sha256_file(weight)
        status = "verified" if actual == item["model_safetensors_sha256"] else "mismatch"
        results.append(
            {
                "kind": "tokenizer",
                "name": token_name,
                "revision": item["revision"],
                "expected": item["model_safetensors_sha256"],
                "actual": actual,
                "status": status,
            }
        )

    output = {
        "benchmark_id": spec.benchmark_id,
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "model_lock": str(root / "model_lock.json"),
        "required_models": required_models,
        "required_tokenizers": required_tokenizers,
        "results": results,
        "all_verified": bool(results) and all(
            item["status"] == "verified" for item in results
        ),
    }
    write_json(root / "model_verification.json", output)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="MarketForge frozen benchmark manager")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    sub = parser.add_subparsers(dest="command", required=True)
    status_parser = sub.add_parser("status", help="Show whether the prospective holdout is ready for collection")
    status_parser.add_argument("--require-ready", action="store_true")
    preregister = sub.add_parser("preregister", help="Create or verify the immutable pre-holdout lock")
    preregister.add_argument("--create", action="store_true", help="Create the lock when it does not exist")
    freeze = sub.add_parser("freeze-data", help="Download official archives and create a verified data lock")
    freeze.add_argument("--force", action="store_true")
    verify = sub.add_parser("verify-models", help="Verify pinned Kronos source and optionally model weights")
    verify.add_argument("--download-weights", action="store_true")
    sub.add_parser("verify-environment", help="Record and verify the exact frozen execution environment")
    sub.add_parser("lock-protocol", help="Freeze spec, model, data, environment and Git state")
    run = sub.add_parser("run", help="Run or resume the matched benchmark")
    run.add_argument("--models", default="marketforge-naive,marketforge-ensemble,marketforge-regime-ensemble,kronos-base")
    run.add_argument("--max-origins", type=int)
    replay = sub.add_parser("verify-results", help="Replay every forecast and compare deterministic evidence")
    replay.add_argument("--models", default="marketforge-naive,marketforge-ensemble,marketforge-regime-ensemble,kronos-base")
    report = sub.add_parser("report", help="Create statistical report and claim-gate decision")
    report.add_argument("--candidate", default="marketforge-regime-ensemble")
    report.add_argument("--comparator", default="kronos-base")

    args = parser.parse_args()
    root = args.root.resolve()
    spec = load_spec(root / "spec.json")
    if args.command == "status":
        ready_at = datetime.fromisoformat(spec.raw["data"]["data_available_not_before"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        prereg_path = root / "preregistration_lock.json"
        prereg_status = "missing"
        if prereg_path.exists():
            prereg = read_json(prereg_path)
            model_lock = read_json(root / "model_lock.json")
            prereg_status = "verified" if not verify_preregistration(prereg, spec, model_lock, code_tree_sha256(PROJECT_ROOT)) else "mismatch"
        result = {
            "benchmark_id": spec.benchmark_id,
            "now": now.isoformat(),
            "data_available_not_before": ready_at.isoformat(),
            "data_collection_ready": now >= ready_at,
            "preregistration": prereg_status,
        }
        if args.require_ready and (now < ready_at or prereg_status != "verified"):
            print(json.dumps(result, indent=2, sort_keys=True))
            raise SystemExit(2)
    elif args.command == "preregister":
        model_lock = read_json(root / "model_lock.json")
        path = root / "preregistration_lock.json"
        commit, dirty = git_state()
        expected = make_preregistration_lock(
            spec, model_lock, code_sha256=code_tree_sha256(PROJECT_ROOT),
            git_commit=commit, git_dirty=dirty,
        )
        if path.exists():
            existing = read_json(path)
            problems = verify_preregistration(existing, spec, model_lock, code_tree_sha256(PROJECT_ROOT))
            if problems:
                raise SystemExit("Preregistration mismatch: " + "; ".join(problems) + " Create a new benchmark ID instead of overwriting it.")
            result = existing
        elif args.create:
            write_json(path, expected)
            result = expected
        else:
            raise SystemExit("Preregistration lock is missing. Repository maintainers must create it before the holdout starts.")
    elif args.command == "freeze-data":
        result = freeze_data(spec, root, force=args.force)
    elif args.command == "verify-models":
        result = verify_models(root, spec, args.download_weights)
    elif args.command == "verify-environment":
        result = build_environment_verification(spec)
        write_json(root / "environment_verification.json", result)
        if not result["all_verified"]:
            raise SystemExit("Execution environment mismatch: " + "; ".join(result["problems"]))
    elif args.command == "lock-protocol":
        model_lock = read_json(root / "model_lock.json")
        data_lock = read_json(root / "data_lock.json")
        prereg_path = root / "preregistration_lock.json"
        if not prereg_path.exists():
            raise SystemExit("Cannot freeze execution protocol: preregistration lock is missing.")
        preregistration = read_json(prereg_path)
        prereg_problems = verify_preregistration(preregistration, spec, model_lock, code_tree_sha256(PROJECT_ROOT))
        if prereg_problems:
            raise SystemExit("Cannot freeze execution protocol: " + "; ".join(prereg_problems))
        verification_path = root / "model_verification.json"
        if not verification_path.exists():
            raise SystemExit("Cannot freeze protocol: run verify-models --download-weights first.")
        model_verification = read_json(verification_path)
        problems = verify_data_lock(root, data_lock, spec)
        if problems:
            raise SystemExit("Cannot freeze protocol: " + "; ".join(problems))
        if not model_verification.get("all_verified"):
            raise SystemExit("Cannot freeze protocol: pinned source, patch and model weights are not all verified.")
        environment_path = root / "environment_verification.json"
        if not environment_path.exists():
            raise SystemExit("Cannot freeze protocol: run verify-environment in the dedicated benchmark environment first.")
        environment_verification = read_json(environment_path)
        environment_problems = verify_environment(environment_verification, spec)
        if environment_problems or not environment_verification.get("all_verified"):
            raise SystemExit("Cannot freeze protocol: " + "; ".join(environment_problems or environment_verification.get("problems", [])))
        commit, dirty = git_state()
        result = make_protocol_lock(
            spec, model_lock, data_lock, commit, dirty,
            code_sha256=code_tree_sha256(PROJECT_ROOT),
            model_verification=model_verification,
            environment_verification=environment_verification,
            preregistration=preregistration,
        )
        write_json(root / "protocol_lock.json", result)
    elif args.command == "run":
        models = [item.strip() for item in args.models.split(",") if item.strip()]
        result = run_benchmark(spec, root, models, max_origins=args.max_origins)
    elif args.command == "verify-results":
        models = [item.strip() for item in args.models.split(",") if item.strip()]
        reference = root / "results" / "predictions.csv"
        replay_path = root / "results" / "replay_predictions.csv"
        if not reference.exists():
            raise SystemExit("Run the frozen benchmark before requesting a replay verification.")
        replay_path.unlink(missing_ok=True)
        run_benchmark(spec, root, models, output_path=replay_path)
        model_lock = read_json(root / "model_lock.json")
        data_lock = read_json(root / "data_lock.json")
        verify_prediction_ledger(reference, spec, model_lock, data_lock)
        verify_prediction_ledger(replay_path, spec, model_lock, data_lock)
        result = compare_replay_ledgers(reference, replay_path)
        result["benchmark_id"] = spec.benchmark_id
        result["reference_sha256"] = sha256_file(reference)
        result["replay_sha256"] = sha256_file(replay_path)
        payload = dict(result); payload.pop("verification_sha256", None)
        from app.benchmark.spec import sha256_json
        result["verification_sha256"] = sha256_json(payload)
        write_json(root / "results" / "replay_verification.json", result)
        if not result["all_verified"]:
            raise SystemExit("Replay verification failed: " + "; ".join(result["problems"]))
    else:
        result = build_report(spec, root, candidate=args.candidate, comparator=args.comparator)
        json_path, md_path = save_report(result, root / "results")
        result = {"claim_gate": result["claim_gate"], "json": str(json_path), "markdown": str(md_path)}
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
