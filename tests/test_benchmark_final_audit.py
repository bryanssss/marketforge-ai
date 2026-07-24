from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
import pytest
from app.benchmark.environment import build_environment_verification, verify_environment
from app.benchmark.spec import load_spec
from app.core.schemas import ForecastSettings


def test_v2_is_deterministic_and_preregistered() -> None:
    spec = load_spec(Path("benchmarks/frozen_v2/spec.json"))
    assert spec.raw["execution"]["device"] == "cpu"
    assert spec.raw["execution"]["deterministic_algorithms"] is True
    assert spec.raw["evaluation"]["origin_hour_utc"] == 0


def test_environment_record_detects_tampering() -> None:
    spec = load_spec(Path("benchmarks/frozen_v2/spec.json"))
    record = build_environment_verification(spec)
    record["python"] = "0.0.0"
    assert verify_environment(record, spec)


def test_forecast_setting_exposes_deterministic_switch() -> None:
    settings = ForecastSettings(engine="kronos", deterministic=True)
    assert settings.deterministic is True
