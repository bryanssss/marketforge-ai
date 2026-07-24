from __future__ import annotations

import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from app.benchmark.data import verify_data_lock
from app.benchmark.environment import verify_environment
from app.benchmark.spec import (
    FrozenSpec,
    code_tree_sha256,
    read_json,
    sha256_json,
    verify_preregistration,
)
from app.core.config import SETTINGS
from app.core.schemas import ForecastSettings
from app.services.forecast_service import create_forecast

PROJECT_ROOT = Path(__file__).resolve().parents[2]
_GENESIS_HASH = "0" * 64
PREDICTION_COLUMNS = [
    "benchmark_id",
    "dataset",
    "symbol",
    "horizon",
    "forecast_max_horizon",
    "origin_timestamp",
    "model",
    "seed",
    "context_end_close",
    "actual_close",
    "actual_return",
    "predicted_close",
    "predicted_return",
    "lower_close",
    "upper_close",
    "absolute_return_error",
    "squared_return_error",
    "direction_correct",
    "covered_80",
    "runtime_seconds",
    "model_revision",
    "tokenizer_revision",
    "protocol_sha256",
    "environment_sha256",
    "dataset_sha256",
    "previous_record_sha256",
    "record_sha256",
]


def _model_settings(
    name: str,
    spec: FrozenSpec,
    model_lock: dict[str, Any],
    seed: int,
    horizon: int,
) -> ForecastSettings:
    evaluation = spec.raw["evaluation"]
    common = dict(
        horizon=horizon,
        lookback=int(evaluation["lookback"]),
        paths=int(evaluation["paths"]),
        block_size=int(evaluation["block_size"]),
        seed=seed,
        calibration=str(evaluation.get("calibration", "none")),
        interval_level=float(evaluation.get("interval_level", 0.80)),
    )
    if name.startswith("marketforge-"):
        baseline = name.removeprefix("marketforge-").replace("-", "_")
        return ForecastSettings(engine="baseline", baseline_model=baseline, **common)
    if name.startswith("kronos-"):
        size = name.removeprefix("kronos-")
        item = model_lock["models"][name]
        tokenizer = model_lock["tokenizers"][item["tokenizer"]]
        return ForecastSettings(
            engine="kronos",
            model_size=size,
            device=spec.raw["execution"]["device"],
            deterministic=bool(spec.raw["execution"]["deterministic_algorithms"]),
            kronos_samples=int(evaluation["kronos_draws"]),
            temperature=float(evaluation["temperature"]),
            top_p=float(evaluation["top_p"]),
            model_revision=item["revision"],
            tokenizer_revision=tokenizer["revision"],
            **common,
        )
    raise ValueError(f"Unknown benchmark model: {name}")


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (float, np.floating)):
        return format(float(value), ".17g")
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    return str(value)


def _record_hash(row: dict[str, str]) -> str:
    fields = [name for name in PREDICTION_COLUMNS if name != "record_sha256"]
    payload = "\x1f".join(f"{name}={row.get(name, '')}" for name in fields)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _expected_revisions(model: str, model_lock: dict[str, Any]) -> tuple[str, str]:
    item = model_lock["models"][model]
    if model.startswith("kronos-"):
        tokenizer = model_lock["tokenizers"][item["tokenizer"]]
        return str(item["revision"]), str(tokenizer["revision"])
    return str(item["revision"]), "not-applicable"


def _existing_state(
    path: Path,
    spec: FrozenSpec,
    model_lock: dict[str, Any],
    data_lock: dict[str, Any],
    *,
    protocol_sha256: str | None = None,
    environment_sha256: str | None = None,
    benchmark_root: Path | None = None,
) -> tuple[set[tuple[str, int, str, str, int]], str]:
    if not path.exists() or path.stat().st_size == 0:
        return set(), _GENESIS_HASH
    allowed_datasets = {str(item["path"]) for item in data_lock["datasets"]}
    allowed_horizons = set(spec.horizons)
    allowed_seeds = {int(value) for value in spec.raw["evaluation"]["seeds"]}
    allowed_models = set(spec.raw["evaluation"]["models"])
    keys: set[tuple[str, int, str, str, int]] = set()
    previous = _GENESIS_HASH
    benchmark_root = benchmark_root or path.parent.parent
    dataset_frames: dict[str, pd.DataFrame] = {}
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != PREDICTION_COLUMNS:
            raise ValueError("Prediction ledger schema does not match the frozen benchmark version.")
        for line_number, row in enumerate(reader, start=2):
            if row["benchmark_id"] != spec.benchmark_id:
                raise ValueError(f"Prediction ledger benchmark ID mismatch on line {line_number}.")
            dataset = row["dataset"]
            model = row["model"]
            horizon = int(row["horizon"])
            seed = int(row["seed"])
            if dataset not in allowed_datasets or model not in allowed_models:
                raise ValueError(f"Unexpected dataset or model on prediction ledger line {line_number}.")
            if horizon not in allowed_horizons or seed not in allowed_seeds:
                raise ValueError(f"Unexpected horizon or seed on prediction ledger line {line_number}.")
            expected_model, expected_tokenizer = _expected_revisions(model, model_lock)
            if row["model_revision"] != expected_model or row["tokenizer_revision"] != expected_tokenizer:
                raise ValueError(f"Model revision mismatch on prediction ledger line {line_number}.")
            dataset_item = next(item for item in data_lock["datasets"] if str(item["path"]) == dataset)
            if row["dataset_sha256"] != str(dataset_item["sha256"]):
                raise ValueError(f"Dataset revision mismatch on prediction ledger line {line_number}.")
            if row["symbol"] != str(dataset_item["symbol"]):
                raise ValueError(f"Dataset symbol mismatch on prediction ledger line {line_number}.")
            if protocol_sha256 is not None and row["protocol_sha256"] != protocol_sha256:
                raise ValueError(f"Protocol binding mismatch on prediction ledger line {line_number}.")
            if environment_sha256 is not None and row["environment_sha256"] != environment_sha256:
                raise ValueError(f"Environment binding mismatch on prediction ledger line {line_number}.")
            origin = pd.Timestamp(row["origin_timestamp"])
            holdout_start = pd.Timestamp(spec.raw["data"]["holdout_start"])
            holdout_end = pd.Timestamp(spec.raw["data"]["holdout_end_exclusive"])
            if not (holdout_start <= origin < holdout_end):
                raise ValueError(f"Origin is outside the holdout on prediction ledger line {line_number}.")
            if origin.hour != int(spec.raw["evaluation"]["origin_hour_utc"]) or origin.minute != 0:
                raise ValueError(f"Origin cadence mismatch on prediction ledger line {line_number}.")
            if int(row["forecast_max_horizon"]) != max(spec.horizons):
                raise ValueError(f"Maximum-horizon mismatch on prediction ledger line {line_number}.")
            if dataset not in dataset_frames:
                frame_path = benchmark_root / dataset
                frame = pd.read_csv(frame_path, parse_dates=["timestamp"])
                frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
                dataset_frames[dataset] = frame.set_index("timestamp", drop=False)
            frame = dataset_frames[dataset]
            if origin not in frame.index:
                raise ValueError(f"Origin timestamp is absent from frozen data on line {line_number}.")
            origin_location = int(frame.index.get_loc(origin))
            actual_location = origin_location + horizon
            if actual_location >= len(frame):
                raise ValueError(f"Actual horizon is absent from frozen data on line {line_number}.")
            context_close = float(frame.iloc[origin_location]["close"])
            actual_close = float(frame.iloc[actual_location]["close"])
            if float(row["context_end_close"]) != context_close or float(row["actual_close"]) != actual_close:
                raise ValueError(f"Frozen actual/context prices changed on prediction ledger line {line_number}.")
            predicted_close = float(row["predicted_close"]); lower = float(row["lower_close"]); upper = float(row["upper_close"])
            actual_return = float(np.log(actual_close / context_close))
            predicted_return = float(np.log(predicted_close / context_close))
            error = predicted_return - actual_return
            expected_values = {
                "actual_return": actual_return, "predicted_return": predicted_return,
                "absolute_return_error": abs(error), "squared_return_error": error * error,
            }
            for field, expected_value in expected_values.items():
                if not np.isclose(float(row[field]), expected_value, rtol=0.0, atol=1e-15):
                    raise ValueError(f"Derived field {field} is inconsistent on prediction ledger line {line_number}.")
            if int(row["direction_correct"]) != int(np.sign(predicted_return) == np.sign(actual_return)):
                raise ValueError(f"Direction metric is inconsistent on prediction ledger line {line_number}.")
            if int(row["covered_80"]) != int(lower <= actual_close <= upper):
                raise ValueError(f"Coverage metric is inconsistent on prediction ledger line {line_number}.")
            if row["previous_record_sha256"] != previous:
                raise ValueError(f"Prediction ledger hash chain is broken on line {line_number}.")
            calculated = _record_hash(row)
            if row["record_sha256"] != calculated:
                raise ValueError(f"Prediction ledger row hash mismatch on line {line_number}.")
            previous = calculated
            key = (dataset, horizon, row["origin_timestamp"], model, seed)
            if key in keys:
                raise ValueError(f"Duplicate prediction ledger key on line {line_number}.")
            keys.add(key)
    return keys, previous


def _verify_locks(spec: FrozenSpec, root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    model_lock = read_json(root / "model_lock.json")
    data_lock = read_json(root / "data_lock.json")
    protocol_lock = read_json(root / "protocol_lock.json")
    problems = verify_data_lock(root, data_lock, spec)
    if problems:
        raise ValueError("Frozen data verification failed: " + "; ".join(problems))
    if protocol_lock.get("status") != "frozen":
        raise ValueError("Execution protocol lock is not frozen.")
    protocol_payload = dict(protocol_lock)
    protocol_hash = protocol_payload.pop("protocol_sha256", None)
    if protocol_hash != sha256_json(protocol_payload):
        raise ValueError("Execution protocol integrity hash is invalid.")

    preregistration_path = root / "preregistration_lock.json"
    if not preregistration_path.exists():
        raise ValueError("Prospective preregistration lock is missing.")
    preregistration = read_json(preregistration_path)
    preregistration_problems = verify_preregistration(
        preregistration, spec, model_lock, code_tree_sha256(PROJECT_ROOT)
    )
    if preregistration_problems:
        raise ValueError(
            "Prospective preregistration verification failed: "
            + "; ".join(preregistration_problems)
        )
    if protocol_lock.get("preregistration_sha256") != preregistration.get(
        "preregistration_sha256"
    ):
        raise ValueError("Execution protocol is not bound to the prospective preregistration.")
    if protocol_lock.get("spec_sha256") != spec.hash:
        raise ValueError("Specification changed after the execution protocol was locked.")
    if protocol_lock.get("model_lock_sha256") != sha256_json(model_lock):
        raise ValueError("Model lock changed after the execution protocol was locked.")
    if protocol_lock.get("data_lock_sha256") != sha256_json(data_lock):
        raise ValueError("Data lock changed after the execution protocol was locked.")

    verification_path = root / "model_verification.json"
    if not verification_path.exists():
        raise ValueError("Model verification record is missing.")
    model_verification = read_json(verification_path)
    if protocol_lock.get("model_verification_sha256") != sha256_json(model_verification):
        raise ValueError("Model verification record changed after protocol locking.")
    environment_path = root / "environment_verification.json"
    if not environment_path.exists():
        raise ValueError("Frozen execution-environment verification record is missing.")
    environment_verification = read_json(environment_path)
    if protocol_lock.get("environment_verification_sha256") != sha256_json(environment_verification):
        raise ValueError("Execution-environment verification changed after protocol locking.")
    if not environment_verification.get("all_verified") or verify_environment(environment_verification, spec):
        raise ValueError("The current execution environment does not match the frozen profile.")
    if not model_verification.get("all_verified"):
        raise ValueError("Pinned source, compatibility patch and model weights are not all verified.")
    if protocol_lock.get("code_sha256") != code_tree_sha256(PROJECT_ROOT):
        raise ValueError("Benchmark-relevant source code changed after preregistration.")
    return model_lock, data_lock


def run_benchmark(
    spec: FrozenSpec,
    root: Path,
    models: Iterable[str],
    *,
    output_path: Path | None = None,
    max_origins: int | None = None,
) -> dict[str, Any]:
    model_lock, data_lock = _verify_locks(spec, root)
    output_path = output_path or root / "results" / "predictions.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    protocol_sha256 = read_json(root / "protocol_lock.json")["protocol_sha256"]
    environment_sha256 = read_json(root / "environment_verification.json")["environment_sha256"]
    existing, previous_hash = _existing_state(
        output_path, spec, model_lock, data_lock,
        protocol_sha256=protocol_sha256, environment_sha256=environment_sha256,
        benchmark_root=root,
    )

    requested_models = list(dict.fromkeys(models))
    required_models = list(spec.raw["evaluation"]["models"])
    if requested_models != required_models:
        raise ValueError(
            "The prospective benchmark must run the pre-registered model list in order: "
            + ", ".join(required_models)
        )
    allowed = set(model_lock["models"])
    unknown = sorted(set(requested_models) - allowed)
    if unknown:
        raise ValueError("Models are not locked: " + ", ".join(unknown))

    holdout_start = pd.Timestamp(spec.raw["data"]["holdout_start"])
    holdout_end = pd.Timestamp(spec.raw["data"]["holdout_end_exclusive"])
    evaluation = spec.raw["evaluation"]
    lookback = int(evaluation["lookback"])
    origin_frequency_hours = int(evaluation["origin_frequency_hours"])
    origin_hour_utc = int(evaluation["origin_hour_utc"])
    seeds = [int(value) for value in evaluation["seeds"]]
    horizons = sorted(spec.horizons)
    max_horizon = max(horizons)
    cap = min(max_origins or SETTINGS.max_benchmark_origins, SETTINGS.max_benchmark_origins)
    forecast_calls = 0
    written = 0
    started = datetime.now(timezone.utc)

    append_header = not output_path.exists() or output_path.stat().st_size == 0
    with output_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PREDICTION_COLUMNS)
        if append_header:
            writer.writeheader()
        for dataset in data_lock["datasets"]:
            data_path = root / dataset["path"]
            frame = pd.read_csv(data_path, parse_dates=["timestamp"])
            frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
            valid_origins = np.flatnonzero(
                (frame["timestamp"] >= holdout_start)
                & (frame["timestamp"] < holdout_end)
            )
            valid = [
                int(index) for index in valid_origins
                if index >= lookback - 1
                and index + max_horizon < len(frame)
                and int(frame["timestamp"].iloc[index].hour) == origin_hour_utc
                and int(frame["timestamp"].iloc[index].minute) == 0
            ]
            if origin_frequency_hours > 24:
                valid = valid[:: max(1, origin_frequency_hours // 24)]
            for origin in valid:
                origin_timestamp = frame["timestamp"].iloc[origin].isoformat()
                context = frame.iloc[origin - lookback + 1 : origin + 1].copy()
                context_close = float(context["close"].iloc[-1])
                for model in requested_models:
                    for seed in seeds:
                        missing_horizons = [
                            horizon
                            for horizon in horizons
                            if (
                                dataset["path"],
                                horizon,
                                origin_timestamp,
                                model,
                                seed,
                            )
                            not in existing
                        ]
                        if not missing_horizons:
                            continue
                        forecast_calls += 1
                        if forecast_calls > cap:
                            raise ValueError(
                                f"Benchmark forecast-call cap exceeded ({cap:,}). "
                                "Increase MARKETFORGE_MAX_BENCHMARK_ORIGINS deliberately."
                            )
                        settings = _model_settings(
                            model, spec, model_lock, seed, max_horizon
                        )
                        import time

                        clock = time.perf_counter()
                        result = create_forecast(context, settings)
                        runtime = time.perf_counter() - clock
                        expected_engine = f"kronos-{model.removeprefix('kronos-')}" if model.startswith("kronos-") else f"baseline-{model.removeprefix('marketforge-').replace('-', '_')}"
                        if result.engine != expected_engine or result.fallback is not None:
                            raise ValueError(f"Frozen benchmark engine mismatch for {model}; automatic fallbacks are forbidden.")
                        expected_model, expected_tokenizer = _expected_revisions(
                            model, model_lock
                        )
                        for horizon in missing_horizons:
                            forecast_row = result.forecast.iloc[horizon - 1]
                            actual_close = float(frame["close"].iloc[origin + horizon])
                            predicted_close = float(forecast_row["close"])
                            lower = float(forecast_row["lower_close"])
                            upper = float(forecast_row["upper_close"])
                            actual_return = float(np.log(actual_close / context_close))
                            predicted_return = float(np.log(predicted_close / context_close))
                            error = predicted_return - actual_return
                            numeric_values = (context_close, actual_close, predicted_close, lower, upper, actual_return, predicted_return, error, runtime)
                            if not all(np.isfinite(value) for value in numeric_values) or min(context_close, actual_close, predicted_close, lower, upper) <= 0 or lower > upper:
                                raise ValueError(f"Non-finite or invalid frozen prediction for {model} at {origin_timestamp}.")
                            raw: dict[str, Any] = {
                                "benchmark_id": spec.benchmark_id,
                                "dataset": dataset["path"],
                                "symbol": dataset["symbol"],
                                "horizon": horizon,
                                "forecast_max_horizon": max_horizon,
                                "origin_timestamp": origin_timestamp,
                                "model": model,
                                "seed": seed,
                                "context_end_close": context_close,
                                "actual_close": actual_close,
                                "actual_return": actual_return,
                                "predicted_close": predicted_close,
                                "predicted_return": predicted_return,
                                "lower_close": lower,
                                "upper_close": upper,
                                "absolute_return_error": abs(error),
                                "squared_return_error": error * error,
                                "direction_correct": int(
                                    np.sign(predicted_return) == np.sign(actual_return)
                                ),
                                "covered_80": int(lower <= actual_close <= upper),
                                "runtime_seconds": runtime,
                                "model_revision": expected_model,
                                "tokenizer_revision": expected_tokenizer,
                                "protocol_sha256": protocol_sha256,
                                "environment_sha256": environment_sha256,
                                "dataset_sha256": dataset["sha256"],
                                "previous_record_sha256": previous_hash,
                            }
                            row = {name: _stringify(raw.get(name)) for name in PREDICTION_COLUMNS}
                            row["record_sha256"] = _record_hash(row)
                            writer.writerow(row)
                            handle.flush()
                            previous_hash = row["record_sha256"]
                            existing.add(
                                (
                                    dataset["path"],
                                    horizon,
                                    origin_timestamp,
                                    model,
                                    seed,
                                )
                            )
                            written += 1
    return {
        "benchmark_id": spec.benchmark_id,
        "started_at": started.isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "models": requested_models,
        "forecast_calls": forecast_calls,
        "new_rows": written,
        "last_record_sha256": previous_hash,
        "output": str(output_path),
    }


def verify_benchmark_locks(spec: FrozenSpec, root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Public verifier used by the report generator before reading results."""
    return _verify_locks(spec, root)


def verify_prediction_ledger(
    path: Path,
    spec: FrozenSpec,
    model_lock: dict[str, Any],
    data_lock: dict[str, Any],
) -> tuple[set[tuple[str, int, str, str, int]], str]:
    """Validate the result chain and every frozen protocol/environment binding."""
    root = path.parent.parent
    protocol_sha256 = read_json(root / "protocol_lock.json")["protocol_sha256"]
    environment_sha256 = read_json(root / "environment_verification.json")["environment_sha256"]
    return _existing_state(
        path, spec, model_lock, data_lock,
        protocol_sha256=protocol_sha256, environment_sha256=environment_sha256,
        benchmark_root=root,
    )


_REPLAY_IGNORED_COLUMNS = {"runtime_seconds", "previous_record_sha256", "record_sha256"}


def compare_replay_ledgers(reference_path: Path, replay_path: Path) -> dict[str, Any]:
    """Compare all deterministic evidence fields while ignoring wall-clock runtime."""
    reference = pd.read_csv(reference_path, dtype=str, keep_default_na=False)
    replay = pd.read_csv(replay_path, dtype=str, keep_default_na=False)
    key = ["dataset", "horizon", "origin_timestamp", "model", "seed"]
    reference = reference.sort_values(key, kind="stable").reset_index(drop=True)
    replay = replay.sort_values(key, kind="stable").reset_index(drop=True)
    columns = [name for name in PREDICTION_COLUMNS if name not in _REPLAY_IGNORED_COLUMNS]
    problems: list[str] = []
    if list(reference.columns) != PREDICTION_COLUMNS or list(replay.columns) != PREDICTION_COLUMNS:
        problems.append("A replay ledger does not use the frozen schema.")
    elif len(reference) != len(replay):
        problems.append(f"Replay row count differs: {len(reference)} versus {len(replay)}.")
    else:
        for column in columns:
            mismatch = reference[column] != replay[column]
            if mismatch.any():
                problems.append(f"Replay differs in {column} on {int(mismatch.sum())} row(s).")
    payload: dict[str, Any] = {
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "reference": str(reference_path),
        "replay": str(replay_path),
        "reference_rows": int(len(reference)),
        "replay_rows": int(len(replay)),
        "compared_columns": columns,
        "ignored_nondeterministic_columns": sorted(_REPLAY_IGNORED_COLUMNS),
        "problems": problems,
        "all_verified": not problems,
    }
    payload["verification_sha256"] = sha256_json(payload)
    return payload
