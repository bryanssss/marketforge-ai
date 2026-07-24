from __future__ import annotations

from app.core.schemas import ComparisonSettings
from app.services.comparison_service import compare_baselines


def test_comparison_ranks_models_and_includes_naive_skill(market_df) -> None:
    result = compare_baselines(
        market_df,
        ComparisonSettings(
            models=["ensemble", "naive"],
            horizon=4,
            lookback=80,
            step=30,
            paths=20,
            block_size=4,
            seed=3,
        ),
    )

    ranking = result["ranking"]
    assert len(ranking) == 2
    assert {row["rank"] for row in ranking} == {1, 2}
    naive = next(row for row in ranking if row["model"] == "naive")
    assert naive["mae_skill_vs_naive_percent"] == 0.0
    assert all(row["evaluations"] > 0 for row in ranking)
