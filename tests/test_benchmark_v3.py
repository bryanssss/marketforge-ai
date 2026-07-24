from __future__ import annotations

from pathlib import Path

from app.benchmark.spec import (
    code_tree_sha256,
    load_spec,
    read_json,
    verify_preregistration,
)

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "benchmarks" / "frozen_v3"
REGISTERED_MODELS = (
    "marketforge-naive,marketforge-ensemble,"
    "marketforge-regime-ensemble,kronos-base"
)


def test_v3_is_the_official_regime_ensemble_protocol() -> None:
    spec = load_spec(BENCHMARK / "spec.json")
    assert spec.benchmark_id == "marketforge-prospective-v3"
    assert spec.raw["evaluation"]["candidate"] == "marketforge-regime-ensemble"
    assert spec.raw["evaluation"]["calibration"] == "empirical"
    assert spec.raw["evaluation"]["interval_level"] == 0.8
    assert spec.raw["execution"]["device"] == "cpu"
    assert spec.raw["execution"]["thread_count"] == 1


def test_v3_preregistration_matches_current_bound_source() -> None:
    spec = load_spec(BENCHMARK / "spec.json")
    model_lock = read_json(BENCHMARK / "model_lock.json")
    preregistration = read_json(BENCHMARK / "preregistration_lock.json")
    assert verify_preregistration(
        preregistration,
        spec,
        model_lock,
        code_tree_sha256(ROOT),
    ) == []


def test_v3_one_click_and_cli_defaults_use_the_registered_candidate() -> None:
    cli = (ROOT / "scripts" / "benchmark.py").read_text(encoding="utf-8")
    windows = (ROOT / "scripts" / "run_frozen_benchmark_windows.bat").read_text(
        encoding="utf-8"
    )
    unix = (ROOT / "scripts" / "run_frozen_benchmark_mac_linux.sh").read_text(
        encoding="utf-8"
    )
    for content in (cli, windows, unix):
        assert REGISTERED_MODELS in content
        assert "--candidate marketforge-regime-ensemble" in content or (
            'report.add_argument("--candidate", default="marketforge-regime-ensemble")'
            in content
        )
