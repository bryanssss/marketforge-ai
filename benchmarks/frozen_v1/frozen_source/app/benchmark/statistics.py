from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class ConfidenceInterval:
    estimate: float
    lower: float
    upper: float


def interval_score(y: np.ndarray, lower: np.ndarray, upper: np.ndarray, alpha: float = 0.2) -> np.ndarray:
    y = np.asarray(y, dtype=float)
    lower = np.asarray(lower, dtype=float)
    upper = np.asarray(upper, dtype=float)
    width = upper - lower
    below = np.where(y < lower, (2.0 / alpha) * (lower - y), 0.0)
    above = np.where(y > upper, (2.0 / alpha) * (y - upper), 0.0)
    return width + below + above


def hac_long_run_variance(values: np.ndarray, lag: int) -> float:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    n = len(values)
    if n < 2:
        return float("nan")
    centered = values - values.mean()
    variance = float(np.dot(centered, centered) / n)
    lag = max(0, min(int(lag), n - 1))
    for offset in range(1, lag + 1):
        covariance = float(np.dot(centered[offset:], centered[:-offset]) / n)
        weight = 1.0 - offset / (lag + 1.0)
        variance += 2.0 * weight * covariance
    return max(variance, 0.0)


def diebold_mariano(loss_candidate: Iterable[float], loss_comparator: Iterable[float], lag: int = 0) -> dict[str, float | int | None]:
    candidate = np.asarray(list(loss_candidate), dtype=float)
    comparator = np.asarray(list(loss_comparator), dtype=float)
    valid = np.isfinite(candidate) & np.isfinite(comparator)
    differential = candidate[valid] - comparator[valid]
    n = len(differential)
    if n < 3:
        return {"n": n, "mean_loss_difference": None, "statistic": None, "p_less": None, "p_two_sided": None, "lag": lag}
    long_run = hac_long_run_variance(differential, lag)
    mean = float(differential.mean())
    if not math.isfinite(long_run) or long_run <= 0:
        statistic = 0.0 if mean == 0 else math.copysign(float("inf"), mean)
    else:
        statistic = mean / math.sqrt(long_run / n)
    p_less = 0.5 * math.erfc(-statistic / math.sqrt(2.0))
    p_two = math.erfc(abs(statistic) / math.sqrt(2.0))
    return {
        "n": n,
        "mean_loss_difference": mean,
        "statistic": float(statistic),
        "p_less": float(p_less),
        "p_two_sided": float(p_two),
        "lag": int(lag),
    }


def moving_block_bootstrap_mean(
    values: Iterable[float],
    *,
    block_length: int,
    repetitions: int,
    seed: int,
    confidence: float = 0.95,
) -> ConfidenceInterval:
    array = np.asarray(list(values), dtype=float)
    array = array[np.isfinite(array)]
    n = len(array)
    if n == 0:
        return ConfidenceInterval(float("nan"), float("nan"), float("nan"))
    block_length = max(1, min(int(block_length), n))
    repetitions = max(100, int(repetitions))
    rng = np.random.default_rng(seed)
    means = np.empty(repetitions, dtype=float)
    max_start = n - block_length
    for rep in range(repetitions):
        sampled: list[float] = []
        while len(sampled) < n:
            start = int(rng.integers(0, max_start + 1))
            sampled.extend(array[start : start + block_length].tolist())
        means[rep] = float(np.mean(sampled[:n]))
    tail = (1.0 - confidence) / 2.0
    lower, upper = np.quantile(means, [tail, 1.0 - tail])
    return ConfidenceInterval(float(array.mean()), float(lower), float(upper))


def holm_adjust(p_values: dict[str, float | None]) -> dict[str, float | None]:
    valid = sorted((key, float(value)) for key, value in p_values.items() if value is not None and math.isfinite(float(value)))
    valid.sort(key=lambda item: item[1])
    count = len(valid)
    adjusted: dict[str, float | None] = {key: None for key in p_values}
    running = 0.0
    for index, (key, value) in enumerate(valid):
        corrected = min(1.0, (count - index) * value)
        running = max(running, corrected)
        adjusted[key] = running
    return adjusted


def _moving_block_resample(values: np.ndarray, block_length: int, rng: np.random.Generator) -> np.ndarray:
    n = len(values)
    block_length = max(1, min(int(block_length), n))
    max_start = n - block_length
    sampled: list[float] = []
    while len(sampled) < n:
        start = int(rng.integers(0, max_start + 1))
        sampled.extend(values[start : start + block_length].tolist())
    return np.asarray(sampled[:n], dtype=float)


def hierarchical_task_bootstrap(
    task_differentials: dict[str, Iterable[float]],
    *,
    repetitions: int,
    seed: int,
    block_length: int = 1,
) -> ConfidenceInterval:
    prepared = {key: np.asarray(list(values), dtype=float) for key, values in task_differentials.items()}
    prepared = {
        key: values[np.isfinite(values)]
        for key, values in prepared.items()
        if np.isfinite(values).any()
    }
    if not prepared:
        return ConfidenceInterval(float("nan"), float("nan"), float("nan"))
    keys = list(prepared)
    observed = float(np.mean([values.mean() for values in prepared.values()]))
    rng = np.random.default_rng(seed)
    estimates = np.empty(max(100, repetitions), dtype=float)
    for rep in range(len(estimates)):
        sampled_keys = rng.choice(keys, size=len(keys), replace=True)
        task_means = []
        for key in sampled_keys:
            values = prepared[str(key)]
            sampled = _moving_block_resample(values, block_length, rng)
            task_means.append(float(sampled.mean()))
        estimates[rep] = float(np.mean(task_means))
    lower, upper = np.quantile(estimates, [0.025, 0.975])
    return ConfidenceInterval(observed, float(lower), float(upper))

