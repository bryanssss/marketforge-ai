from __future__ import annotations

import json
import os
import platform
from pathlib import Path

import numpy as np
import pandas as pd

from app.benchmark.data import sha256_file
from app.benchmark.report import build_report, save_report
from app.benchmark.runner import run_benchmark
from app.benchmark.spec import (
    code_tree_sha256,
    load_spec,
    make_preregistration_lock,
    make_protocol_lock,
    write_json,
)


def _mini_benchmark(tmp_path: Path) -> tuple[Path, object]:
    root = tmp_path / "bench"
    (root / "data" / "canonical").mkdir(parents=True)
    timestamps = pd.date_range("2026-01-01", periods=96, freq="h", tz="UTC")
    close = 100 * np.exp(np.cumsum(np.full(96, 0.0005)))
    frame = pd.DataFrame({
        "timestamp": timestamps,
        "open": close * 0.9998,
        "high": close * 1.001,
        "low": close * 0.999,
        "close": close,
        "volume": np.full(96, 10.0),
        "amount": close * 10,
    })
    data_path = root / "data" / "canonical" / "TEST-1h.csv"
    frame.to_csv(data_path, index=False)
    spec_raw = {
        "benchmark_id": "test-frozen",
        "version": "1",
        "frozen_at": "2026-01-01T00:00:00Z",
        "data": {
            "provider": "binance-public-data", "symbols": ["TEST"], "interval": "1h",
            "context_start": "2026-01-01T00:00:00Z", "holdout_start": "2026-01-03T00:00:00Z",
            "holdout_end_exclusive": "2026-01-05T00:00:00Z",
            "data_available_not_before": "2026-01-06T00:00:00Z"
        },
        "execution": {"device": "cpu", "deterministic_algorithms": True, "thread_count": 1, "python_major_minor": ".".join(platform.python_version_tuple()[:2]), "required_packages": {"numpy": __import__("importlib.metadata").metadata.version("numpy")}},
        "evaluation": {
            "lookback": 40, "horizons": [1], "origin_frequency_hours": 24, "origin_hour_utc": 0, "paths": 20, "block_size": 4,
            "seeds": [1], "kronos_draws": 1, "temperature": 1.0, "top_p": 0.9,
            "models": ["marketforge-naive", "marketforge-ensemble"],
            "candidate": "marketforge-ensemble", "primary_comparator": "marketforge-naive",
            "sanity_comparator": "marketforge-naive"
        },
        "statistics": {"block_length": 2, "bootstrap_repetitions": 200, "hierarchical_bootstrap_repetitions": 200, "seed": 4},
        "claim_gate": {
            "alpha": 0.05, "minimum_observations_per_task": 2, "minimum_task_win_rate": 0,
            "minimum_significant_task_win_rate": 0, "minimum_mean_relative_mae_improvement": -1,
            "global_hierarchical_ci_upper_must_be_below_zero": True,
            "all_tasks_must_be_complete": True, "data_and_protocol_locks_must_be_verified": True,
            "must_beat_sanity_comparator": True, "maximum_mean_absolute_coverage_error_80": 1.0
        }
    }
    write_json(root / "spec.json", spec_raw)
    model_lock = {
        "kronos_source": {"commit": "x"},
        "models": {
            "marketforge-naive": {"revision": "marketforge-ai-0.4.0", "tokenizer": None},
            "marketforge-ensemble": {"revision": "marketforge-ai-0.4.0", "tokenizer": None}
        },
        "tokenizers": {}
    }
    archive_path = root / "data" / "provider" / "TEST-1h-2026-01.zip"
    checksum_path = Path(str(archive_path) + ".CHECKSUM")
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path.write_bytes(b"test-archive")
    archive_hash = sha256_file(archive_path)
    checksum_path.write_text(archive_hash + "  TEST-1h-2026-01.zip\n", encoding="utf-8")
    data_lock = {
        "benchmark_id": "test-frozen", "status": "verified",
        "provider_checksum_verified": True, "archives": [{
            "symbol": "TEST", "month": "2026-01",
            "archive_path": str(archive_path.relative_to(root)),
            "checksum_path": str(checksum_path.relative_to(root)),
            "provider_sha256": archive_hash, "downloaded_sha256": archive_hash,
            "checksum_file_sha256": sha256_file(checksum_path)
        }], "datasets": [{
            "symbol": "TEST", "interval": "1h", "path": "data/canonical/TEST-1h.csv",
            "sha256": sha256_file(data_path), "rows": len(frame), "start": timestamps[0].isoformat(), "end": timestamps[-1].isoformat()
        }]
    }
    model_verification = {"all_verified": True, "results": [{"status": "verified"}]}
    from app.benchmark.environment import build_environment_verification

    for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[name] = "1"
    try:
        import torch
    except ImportError:
        pass
    else:
        torch.set_num_threads(1)
    environment_verification = build_environment_verification(load_spec(root / "spec.json"))
    write_json(root / "model_lock.json", model_lock)
    write_json(root / "data_lock.json", data_lock)
    write_json(root / "model_verification.json", model_verification)
    write_json(root / "environment_verification.json", environment_verification)
    spec = load_spec(root / "spec.json")
    project_root = Path(__file__).resolve().parents[1]
    code_hash = code_tree_sha256(project_root)
    preregistration = make_preregistration_lock(
        spec, model_lock, code_sha256=code_hash, git_commit=None, git_dirty=None
    )
    write_json(root / "preregistration_lock.json", preregistration)
    write_json(
        root / "protocol_lock.json",
        make_protocol_lock(
            spec, model_lock, data_lock, None, None,
            code_sha256=code_hash,
            model_verification=model_verification,
            environment_verification=environment_verification,
            preregistration=preregistration,
        ),
    )
    return root, spec


def test_runner_resumes_and_report_blocks_incomplete_comparator(tmp_path: Path) -> None:
    root, spec = _mini_benchmark(tmp_path)
    first = run_benchmark(spec, root, ["marketforge-naive", "marketforge-ensemble"])
    second = run_benchmark(spec, root, ["marketforge-naive", "marketforge-ensemble"])
    assert first["new_rows"] > 0
    assert second["new_rows"] == 0
    report = build_report(spec, root, candidate="marketforge-ensemble", comparator="marketforge-naive")
    assert report["completed_tasks"] == 1
    json_path, markdown_path = save_report(report, root / "results")
    assert json_path.exists() and markdown_path.exists()


def test_report_marks_prefix_as_incomplete(tmp_path: Path) -> None:
    root, spec = _mini_benchmark(tmp_path)
    run_benchmark(spec, root, ["marketforge-naive", "marketforge-ensemble"])
    path = root / "results" / "predictions.csv"
    lines = path.read_text(encoding="utf-8").splitlines()
    # Header plus one matched origin (naive and ensemble). The chain remains a
    # valid prefix, but there is not enough evidence for a result.
    path.write_text("\n".join(lines[:3]) + "\n", encoding="utf-8")
    report = build_report(
        spec, root, candidate="marketforge-ensemble", comparator="marketforge-naive"
    )
    assert report["claim_gate"]["status"] == "INCOMPLETE"


def test_replay_comparison_detects_prediction_change(tmp_path: Path) -> None:
    from app.benchmark.runner import compare_replay_ledgers

    root, spec = _mini_benchmark(tmp_path)
    run_benchmark(spec, root, ["marketforge-naive", "marketforge-ensemble"])
    reference = root / "results" / "predictions.csv"
    replay = root / "results" / "replay.csv"
    replay.write_bytes(reference.read_bytes())
    assert compare_replay_ledgers(reference, replay)["all_verified"] is True
    frame = pd.read_csv(replay)
    frame.loc[0, "predicted_close"] *= 1.01
    frame.to_csv(replay, index=False)
    result = compare_replay_ledgers(reference, replay)
    assert result["all_verified"] is False
    assert any("predicted_close" in problem for problem in result["problems"])
