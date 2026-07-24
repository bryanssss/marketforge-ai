from __future__ import annotations

import hashlib
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from app.benchmark.data import sha256_file
from app.benchmark.runner import verify_benchmark_locks, verify_prediction_ledger
from app.benchmark.spec import FrozenSpec, read_json, sha256_json, write_json
from app.benchmark.statistics import (
    diebold_mariano,
    hierarchical_task_bootstrap,
    holm_adjust,
    interval_score,
    moving_block_bootstrap_mean,
)

_ORIGIN_KEY = ["dataset", "symbol", "horizon", "origin_timestamp"]


def _aggregate_model(frame: pd.DataFrame, model: str) -> pd.DataFrame:
    selected = frame[frame["model"] == model].copy()
    if selected.empty:
        return selected
    grouped = selected.groupby(_ORIGIN_KEY, sort=True, as_index=False).agg(
        actual_return=("actual_return", "first"),
        actual_close=("actual_close", "first"),
        context_end_close=("context_end_close", "first"),
        predicted_return=("predicted_return", "mean"),
        lower_close=("lower_close", "mean"),
        upper_close=("upper_close", "mean"),
        runtime_seconds=("runtime_seconds", "mean"),
        seed_runs=("seed", "nunique"),
    )
    grouped["predicted_close"] = grouped["context_end_close"] * np.exp(
        grouped["predicted_return"]
    )
    error = grouped["predicted_return"] - grouped["actual_return"]
    grouped["absolute_return_error"] = error.abs()
    grouped["squared_return_error"] = error**2
    return grouped


def _metrics(frame: pd.DataFrame) -> dict[str, float | int]:
    actual = frame["actual_return"].to_numpy(float)
    predicted = frame["predicted_return"].to_numpy(float)
    lower_return = np.log(
        frame["lower_close"].to_numpy(float)
        / frame["context_end_close"].to_numpy(float)
    )
    upper_return = np.log(
        frame["upper_close"].to_numpy(float)
        / frame["context_end_close"].to_numpy(float)
    )
    return {
        "n": int(len(frame)),
        "mae": float(np.mean(np.abs(predicted - actual))),
        "rmse": float(np.sqrt(np.mean((predicted - actual) ** 2))),
        "directional_accuracy": float(np.mean(np.sign(predicted) == np.sign(actual))),
        "coverage_80": float(np.mean((actual >= lower_return) & (actual <= upper_return))),
        "mean_interval_score_80": float(
            np.mean(interval_score(actual, lower_return, upper_return))
        ),
        "mean_interval_width": float(np.mean(upper_return - lower_return)),
        "mean_runtime_seconds": float(frame["runtime_seconds"].mean()),
    }


def _matched(
    frame: pd.DataFrame, candidate: str, comparator: str
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    left = _aggregate_model(frame, candidate)
    right = _aggregate_model(frame, comparator)
    merged = left.merge(
        right, on=_ORIGIN_KEY, suffixes=("_candidate", "_comparator"),
        how="inner", validate="one_to_one",
    )
    for column in ("actual_return", "actual_close", "context_end_close"):
        if not np.array_equal(merged[f"{column}_candidate"].to_numpy(), merged[f"{column}_comparator"].to_numpy()):
            raise ValueError(f"Matched models disagree on frozen {column}; the ledger is invalid.")
    return left, right, merged


def _pair_evidence(
    matched: pd.DataFrame,
    spec: FrozenSpec,
) -> tuple[list[dict[str, Any]], dict[str, np.ndarray], dict[str, float | None]]:
    task_reports: list[dict[str, Any]] = []
    normalised_differentials: dict[str, np.ndarray] = {}
    p_values: dict[str, float | None] = {}
    stats = spec.raw["statistics"]
    origin_step = int(spec.raw["evaluation"].get("origin_frequency_hours", spec.raw["evaluation"].get("origin_step", 24)))

    for (symbol, horizon), task in matched.groupby(["symbol", "horizon"], sort=True):
        task = task.sort_values("origin_timestamp", kind="stable")
        task_id = f"{symbol}-h{int(horizon)}"
        candidate_loss = task["absolute_return_error_candidate"].to_numpy(float)
        comparator_loss = task["absolute_return_error_comparator"].to_numpy(float)
        differential = candidate_loss - comparator_loss
        comparator_scale = max(float(comparator_loss.mean()), np.finfo(float).eps)
        normalised_differentials[task_id] = differential / comparator_scale
        lag = max(0, math.ceil(int(horizon) / origin_step) - 1)
        dm = diebold_mariano(candidate_loss, comparator_loss, lag=lag)
        ci = moving_block_bootstrap_mean(
            differential,
            block_length=int(stats["block_length"]),
            repetitions=int(stats["bootstrap_repetitions"]),
            seed=int(stats["seed"])
            + int.from_bytes(hashlib.sha256(task_id.encode("utf-8")).digest()[:4], "big"),
        )
        p_values[task_id] = dm["p_less"] if isinstance(dm["p_less"], float) else None
        candidate_view = pd.DataFrame(
            {
                "actual_return": task["actual_return_candidate"],
                "predicted_return": task["predicted_return_candidate"],
                "lower_close": task["lower_close_candidate"],
                "upper_close": task["upper_close_candidate"],
                "context_end_close": task["context_end_close_candidate"],
                "runtime_seconds": task["runtime_seconds_candidate"],
            }
        )
        comparator_view = pd.DataFrame(
            {
                "actual_return": task["actual_return_comparator"],
                "predicted_return": task["predicted_return_comparator"],
                "lower_close": task["lower_close_comparator"],
                "upper_close": task["upper_close_comparator"],
                "context_end_close": task["context_end_close_comparator"],
                "runtime_seconds": task["runtime_seconds_comparator"],
            }
        )
        task_reports.append(
            {
                "task": task_id,
                "symbol": symbol,
                "horizon": int(horizon),
                "matched_n": int(len(task)),
                "candidate": _metrics(candidate_view),
                "comparator": _metrics(comparator_view),
                "mae_difference_candidate_minus_comparator": float(differential.mean()),
                "mae_relative_improvement": float(
                    1.0 - candidate_loss.mean() / comparator_loss.mean()
                )
                if comparator_loss.mean() > 0
                else None,
                "bootstrap_95_ci": {"lower": ci.lower, "upper": ci.upper},
                "diebold_mariano": dm,
            }
        )
    return task_reports, normalised_differentials, p_values


def build_report(
    spec: FrozenSpec,
    root: Path,
    *,
    candidate: str,
    comparator: str,
    predictions_path: Path | None = None,
) -> dict[str, Any]:
    evaluation = spec.raw["evaluation"]
    if candidate != evaluation["candidate"] or comparator != evaluation["primary_comparator"]:
        raise ValueError(
            "The prospective report must use the pre-registered candidate and primary comparator."
        )
    predictions_path = predictions_path or root / "results" / "predictions.csv"
    if not predictions_path.exists():
        raise ValueError(f"Predictions file does not exist: {predictions_path}")
    model_lock, data_lock = verify_benchmark_locks(spec, root)
    _, ledger_tail = verify_prediction_ledger(
        predictions_path, spec, model_lock, data_lock
    )
    frame = pd.read_csv(predictions_path)
    required = {
        "model",
        "dataset",
        "symbol",
        "horizon",
        "origin_timestamp",
        "seed",
        "actual_return",
        "predicted_return",
        "absolute_return_error",
        "squared_return_error",
        "lower_close",
        "upper_close",
        "context_end_close",
        "runtime_seconds",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError("Predictions file is missing columns: " + ", ".join(missing))

    _, _, matched = _matched(frame, candidate, comparator)
    task_reports, task_differentials, p_values = _pair_evidence(matched, spec)
    adjusted = holm_adjust(p_values)
    for task in task_reports:
        task["holm_adjusted_p_less"] = adjusted[task["task"]]

    stats = spec.raw["statistics"]
    global_ci = hierarchical_task_bootstrap(
        task_differentials,
        repetitions=int(stats["hierarchical_bootstrap_repetitions"]),
        seed=int(stats["seed"]),
        block_length=int(stats["block_length"]),
    )

    sanity_name = evaluation["sanity_comparator"]
    _, _, sanity_matched = _matched(frame, candidate, sanity_name)
    _, sanity_differentials, _ = _pair_evidence(sanity_matched, spec)
    sanity_ci = hierarchical_task_bootstrap(
        sanity_differentials,
        repetitions=int(stats["hierarchical_bootstrap_repetitions"]),
        seed=int(stats["seed"]) + 1,
        block_length=int(stats["block_length"]),
    )

    gate = spec.raw["claim_gate"]
    replay_missing = False
    replay_invalid_reason: str | None = None
    if gate.get("independent_replay_must_match"):
        replay_path = root / "results" / "replay_verification.json"
        if not replay_path.exists():
            replay_missing = True
        else:
            replay_record = read_json(replay_path)
            replay_payload = dict(replay_record)
            replay_hash = replay_payload.pop("verification_sha256", None)
            if replay_hash != sha256_json(replay_payload):
                replay_invalid_reason = "Replay-verification integrity hash is invalid."
            elif replay_record.get("reference_sha256") != sha256_file(predictions_path):
                replay_invalid_reason = "Replay verification is not bound to the current prediction ledger."
            elif replay_record.get("benchmark_id") != spec.benchmark_id:
                replay_invalid_reason = "Replay verification belongs to a different benchmark."
            elif replay_record.get("all_verified") is not True:
                replay_invalid_reason = "Deterministic replay did not reproduce every frozen prediction field."
    expected_tasks = len(spec.assets) * len(spec.horizons)
    complete_tasks = len(task_reports)
    wins = [
        task
        for task in task_reports
        if task["mae_difference_candidate_minus_comparator"] < 0
    ]
    significant_wins = [
        task
        for task in task_reports
        if task["mae_difference_candidate_minus_comparator"] < 0
        and task["holm_adjusted_p_less"] is not None
        and task["holm_adjusted_p_less"] <= float(gate["alpha"])
        and task["bootstrap_95_ci"]["upper"] < 0
    ]
    relative_improvements = [
        task["mae_relative_improvement"]
        for task in task_reports
        if task["mae_relative_improvement"] is not None
    ]
    mean_relative_improvement = (
        float(np.mean(relative_improvements)) if relative_improvements else float("nan")
    )
    win_rate = len(wins) / expected_tasks if expected_tasks else 0.0
    significant_win_rate = (
        len(significant_wins) / expected_tasks if expected_tasks else 0.0
    )
    mean_coverage_error = (
        float(
            np.mean(
                [abs(float(task["candidate"]["coverage_80"]) - 0.8) for task in task_reports]
            )
        )
        if task_reports
        else float("nan")
    )

    incomplete_reasons: list[str] = []
    performance_reasons: list[str] = []
    if complete_tasks != expected_tasks:
        incomplete_reasons.append(f"Only {complete_tasks} of {expected_tasks} tasks have matched predictions.")
    if replay_missing:
        incomplete_reasons.append("The required deterministic replay verification has not been completed.")
    if replay_invalid_reason:
        performance_reasons.append(replay_invalid_reason)
    expected_seed_runs = len(evaluation["seeds"])
    if any(task["matched_n"] < int(gate["minimum_observations_per_task"]) for task in task_reports):
        incomplete_reasons.append("At least one task has too few unique matched forecast origins.")
    candidate_agg = _aggregate_model(frame, candidate)
    comparator_agg = _aggregate_model(frame, comparator)
    if (not candidate_agg.empty and (candidate_agg["seed_runs"] != expected_seed_runs).any()) or (not comparator_agg.empty and (comparator_agg["seed_runs"] != expected_seed_runs).any()):
        incomplete_reasons.append("At least one matched origin is missing a pre-registered seed run.")
    if not math.isfinite(global_ci.upper) or global_ci.upper >= 0:
        performance_reasons.append("The hierarchical 95% confidence interval does not show a global relative loss reduction against Kronos.")
    if win_rate < float(gate["minimum_task_win_rate"]): performance_reasons.append("Task win rate is below the pre-registered threshold.")
    if significant_win_rate < float(gate["minimum_significant_task_win_rate"]): performance_reasons.append("Holm-adjusted significant task win rate is below the threshold.")
    if not math.isfinite(mean_relative_improvement) or mean_relative_improvement < float(gate["minimum_mean_relative_mae_improvement"]): performance_reasons.append("Mean relative MAE improvement is below the pre-registered minimum.")
    if not math.isfinite(mean_coverage_error) or mean_coverage_error > float(gate["maximum_mean_absolute_coverage_error_80"]): performance_reasons.append("Candidate central-80% interval calibration error is too large.")
    if gate.get("must_beat_sanity_comparator") and (not math.isfinite(sanity_ci.upper) or sanity_ci.upper >= 0):
        performance_reasons.append("The candidate did not beat the naive sanity comparator with a 95% confidence interval entirely below zero.")
    status = "INCOMPLETE" if incomplete_reasons else ("PASS" if not performance_reasons else "FAIL")
    reasons = incomplete_reasons + ([] if incomplete_reasons else performance_reasons)
    return {
        "benchmark_id": spec.benchmark_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidate": candidate,
        "comparator": comparator,
        "sanity_comparator": sanity_name,
        "prediction_rows": int(len(frame)),
        "predictions_sha256": sha256_file(predictions_path),
        "ledger_tail_sha256": ledger_tail,
        "replay_verification_required": bool(gate.get("independent_replay_must_match")),
        "replay_verification_status": (
            "missing" if replay_missing else ("invalid" if replay_invalid_reason else "verified")
        ),
        "matched_unique_origins": int(len(matched)),
        "expected_tasks": expected_tasks,
        "completed_tasks": complete_tasks,
        "task_win_rate": win_rate,
        "significant_task_win_rate": significant_win_rate,
        "mean_relative_mae_improvement": mean_relative_improvement,
        "mean_absolute_coverage_error_80": mean_coverage_error,
        "global_mean_relative_mae_difference": global_ci.estimate,
        "global_hierarchical_block_bootstrap_95_ci": {
            "lower": global_ci.lower,
            "upper": global_ci.upper,
        },
        "sanity_global_mean_relative_mae_difference": sanity_ci.estimate,
        "sanity_hierarchical_block_bootstrap_95_ci": {
            "lower": sanity_ci.lower,
            "upper": sanity_ci.upper,
        },
        "claim_gate": {"status": status, "reasons": reasons, "rules": gate},
        "tasks": task_reports,
    }


def markdown_report(report: dict[str, Any]) -> str:
    gate = report["claim_gate"]
    global_ci = report["global_hierarchical_block_bootstrap_95_ci"]
    sanity_ci = report["sanity_hierarchical_block_bootstrap_95_ci"]
    lines = [
        f"# Prospective Frozen Benchmark Report — {report['benchmark_id']}",
        "",
        f"**Candidate:** `{report['candidate']}`  ",
        f"**Primary comparator:** `{report['comparator']}`  ",
        f"**Sanity comparator:** `{report['sanity_comparator']}`  ",
        f"**Claim gate:** **{gate['status']}**",
        "",
        "## Global Result",
        "",
        f"- Unique matched origin-task rows: {report['matched_unique_origins']:,}",
        f"- Completed tasks: {report['completed_tasks']} / {report['expected_tasks']}",
        f"- Task win rate: {report['task_win_rate']:.1%}",
        f"- Holm-significant task win rate: {report['significant_task_win_rate']:.1%}",
        f"- Mean relative MAE improvement: {report['mean_relative_mae_improvement']:.2%}",
        f"- Mean absolute 80% coverage error: {report['mean_absolute_coverage_error_80']:.2%}",
        f"- Global relative MAE difference: {report['global_mean_relative_mae_difference']:.4%}",
        f"- Hierarchical block-bootstrap 95% CI: [{global_ci['lower']:.4%}, {global_ci['upper']:.4%}]",
        f"- Relative MAE difference versus naive: {report['sanity_global_mean_relative_mae_difference']:.4%}",
        f"- Naive-comparison 95% CI: [{sanity_ci['lower']:.4%}, {sanity_ci['upper']:.4%}]",
        f"- Prediction ledger SHA-256: `{report['predictions_sha256']}`",
        f"- Ledger chain tail: `{report['ledger_tail_sha256']}`",
        f"- Deterministic replay: {report['replay_verification_status']}",
        "",
        "## Claim-Gate Reasons",
        "",
    ]
    lines.extend(
        [f"- {reason}" for reason in gate["reasons"]]
        or ["- All pre-registered rules passed."]
    )
    lines.extend(
        [
            "",
            "## Task Results",
            "",
            "| Task | N | Candidate MAE | Kronos MAE | Relative improvement | Adjusted p | Bootstrap CI |",
            "|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    for task in report["tasks"]:
        relative = task["mae_relative_improvement"]
        p_value = task["holm_adjusted_p_less"]
        ci = task["bootstrap_95_ci"]
        relative_text = f"{relative:.2%}" if relative is not None else "n/a"
        p_text = f"{p_value:.5f}" if p_value is not None else "n/a"
        lines.append(
            f"| {task['task']} | {task['matched_n']} | {task['candidate']['mae']:.8f} | "
            f"{task['comparator']['mae']:.8f} | {relative_text} | {p_text} | "
            f"[{ci['lower']:.8f}, {ci['upper']:.8f}] |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A PASS means the candidate met every rule written before the holdout began. It does not guarantee trading profitability or future performance.",
            "",
        ]
    )
    return "\n".join(lines)


def save_report(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "benchmark_report.json"
    markdown_path = output_dir / "benchmark_report.md"
    write_json(json_path, report)
    markdown_path.write_text(markdown_report(report), encoding="utf-8")
    return json_path, markdown_path
