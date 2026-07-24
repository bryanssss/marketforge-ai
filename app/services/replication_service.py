from __future__ import annotations

import io
from typing import Any

import numpy as np
import pandas as pd

from app.benchmark.statistics import diebold_mariano, moving_block_bootstrap_mean
from app.core.schemas import ReplicationRequest

_REQUIRED = {"origin", "model", "actual", "prediction"}


def analyse_external_replication(content: bytes, settings: ReplicationRequest) -> dict[str, Any]:
    if not content or b"\x00" in content[:4096]:
        raise ValueError("The replication ledger is empty or binary.")
    try:
        frame = pd.read_csv(io.BytesIO(content))
    except Exception as exc:
        raise ValueError("The replication ledger could not be parsed as CSV.") from exc
    frame.columns = [str(column).strip().lower() for column in frame.columns]
    missing = sorted(_REQUIRED - set(frame.columns))
    if missing:
        raise ValueError("Missing replication column(s): " + ", ".join(missing))
    frame["origin"] = pd.to_datetime(frame["origin"], errors="coerce", utc=True)
    for column in ("actual", "prediction"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["origin", "model", "actual", "prediction"])
    frame = frame[frame["actual"] > 0]
    if frame.empty:
        raise ValueError("The replication ledger has no valid observations.")

    candidate = frame[frame["model"] == settings.candidate_name].copy()
    comparator = frame[frame["model"] == settings.comparator_name].copy()
    matched = candidate.merge(comparator, on="origin", suffixes=("_candidate", "_comparator"))
    if len(matched) < 10:
        raise ValueError("At least 10 matched forecast origins are required.")
    actual = matched["actual_candidate"].to_numpy(dtype=float)
    if not np.allclose(actual, matched["actual_comparator"].to_numpy(dtype=float), rtol=1e-10, atol=1e-12):
        raise ValueError("Candidate and comparator rows disagree about actual values.")
    candidate_error = np.abs(np.log(matched["prediction_candidate"].to_numpy(dtype=float) / actual))
    comparator_error = np.abs(np.log(matched["prediction_comparator"].to_numpy(dtype=float) / actual))
    differential = candidate_error - comparator_error
    dm = diebold_mariano(candidate_error, comparator_error, lag=max(0, settings.block_size - 1))
    interval = moving_block_bootstrap_mean(
        differential,
        block_length=settings.block_size,
        repetitions=settings.bootstrap_samples,
        seed=settings.seed,
        confidence=1.0 - settings.alpha,
    )
    candidate_mae = float(candidate_error.mean())
    comparator_mae = float(comparator_error.mean())
    return {
        "candidate": settings.candidate_name,
        "comparator": settings.comparator_name,
        "matched_origins": len(matched),
        "candidate_mae_log_return": round(candidate_mae, 8),
        "comparator_mae_log_return": round(comparator_mae, 8),
        "relative_improvement_percent": round((comparator_mae - candidate_mae) / max(comparator_mae, 1e-12) * 100.0, 4),
        "mean_loss_difference": round(float(differential.mean()), 8),
        "bootstrap_confidence_interval": {
            "lower": round(interval.lower, 8),
            "estimate": round(interval.estimate, 8),
            "upper": round(interval.upper, 8),
            "confidence": 1.0 - settings.alpha,
        },
        "diebold_mariano": dm,
        "candidate_better_at_registered_alpha": bool(interval.upper < 0 and float(dm.get("p_less") or 1.0) < settings.alpha),
        "notes": [
            "This tool checks a standard external prediction ledger; it does not certify dataset independence or model training cut-offs.",
            "Independent replication should publish the ledger, source revisions, data hashes and preregistered analysis rules.",
        ],
    }
