from __future__ import annotations

import numpy as np

from app.benchmark.statistics import (
    diebold_mariano,
    hierarchical_task_bootstrap,
    holm_adjust,
    interval_score,
    moving_block_bootstrap_mean,
)


def test_interval_score_rewards_covered_narrow_interval() -> None:
    values = interval_score(np.array([1.0, 3.0]), np.array([0.5, 0.5]), np.array([1.5, 1.5]))
    assert values[0] == 1.0
    assert values[1] > values[0]


def test_dm_detects_consistently_lower_candidate_loss() -> None:
    result = diebold_mariano([0.1, 0.2, 0.1, 0.2, 0.1], [0.5, 0.6, 0.5, 0.6, 0.5])
    assert result["mean_loss_difference"] < 0
    assert result["p_less"] < 0.05


def test_moving_block_bootstrap_is_reproducible() -> None:
    first = moving_block_bootstrap_mean([-1, -2, -1, -2, -1], block_length=2, repetitions=500, seed=3)
    second = moving_block_bootstrap_mean([-1, -2, -1, -2, -1], block_length=2, repetitions=500, seed=3)
    assert first == second
    assert first.upper < 0


def test_holm_adjustment_is_monotonic() -> None:
    adjusted = holm_adjust({"a": 0.01, "b": 0.03, "c": 0.2, "missing": None})
    assert adjusted["a"] <= adjusted["b"] <= adjusted["c"]
    assert adjusted["missing"] is None


def test_hierarchical_bootstrap_detects_negative_task_effect() -> None:
    result = hierarchical_task_bootstrap({"a": [-0.2] * 20, "b": [-0.1] * 20}, repetitions=500, seed=7)
    assert result.upper < 0
