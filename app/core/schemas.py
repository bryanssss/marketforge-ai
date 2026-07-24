from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

BaselineModel = Literal["block_bootstrap", "drift", "naive", "ensemble"]


class ForecastSettings(BaseModel):
    engine: Literal["auto", "baseline", "kronos"] = "auto"
    baseline_model: BaselineModel = "ensemble"
    horizon: int = Field(default=24, ge=1, le=240)
    lookback: int = Field(default=256, ge=40, le=2048)
    paths: int = Field(default=200, ge=20, le=1000)
    block_size: int = Field(default=8, ge=1, le=64)
    seed: int = Field(default=42, ge=0, le=2_147_483_647)
    model_size: Literal["mini", "small", "base"] = "small"
    device: Literal["auto", "cpu", "cuda", "mps"] = "auto"
    temperature: float = Field(default=1.0, ge=0.1, le=2.0)
    top_p: float = Field(default=0.9, ge=0.1, le=1.0)
    kronos_samples: int = Field(default=4, ge=1, le=16)
    model_revision: str | None = Field(default=None, min_length=7, max_length=64)
    tokenizer_revision: str | None = Field(default=None, min_length=7, max_length=64)
    deterministic: bool = False

    @model_validator(mode="after")
    def validate_context(self) -> "ForecastSettings":
        if self.block_size > self.lookback // 2:
            raise ValueError("Block size must be no more than half of the lookback window.")
        return self


class BacktestSettings(BaseModel):
    baseline_model: BaselineModel = "ensemble"
    horizon: int = Field(default=12, ge=1, le=120)
    lookback: int = Field(default=160, ge=40, le=1024)
    step: int = Field(default=12, ge=1, le=120)
    paths: int = Field(default=100, ge=20, le=300)
    block_size: int = Field(default=8, ge=1, le=64)
    threshold_percent: float = Field(default=0.25, ge=0, le=25)
    fee_percent: float = Field(default=0.10, ge=0, le=5)
    slippage_percent: float = Field(default=0.05, ge=0, le=5)
    position_size_percent: float = Field(default=100, gt=0, le=100)
    direction: Literal["long_short", "long_only", "short_only"] = "long_short"
    allow_overlap: bool = False
    execution_delay: int = Field(default=1, ge=1, le=5)
    stop_loss_percent: float | None = Field(default=None, gt=0, le=50)
    take_profit_percent: float | None = Field(default=None, gt=0, le=100)
    seed: int = Field(default=42, ge=0, le=2_147_483_647)

    @model_validator(mode="after")
    def validate_backtest(self) -> "BacktestSettings":
        if self.block_size > self.lookback // 2:
            raise ValueError("Block size must be no more than half of the lookback window.")
        return self


class ComparisonSettings(BaseModel):
    models: list[BaselineModel] = Field(
        default_factory=lambda: ["ensemble", "block_bootstrap", "drift", "naive"],
        min_length=1,
        max_length=4,
    )
    horizon: int = Field(default=12, ge=1, le=120)
    lookback: int = Field(default=160, ge=40, le=1024)
    step: int = Field(default=24, ge=1, le=240)
    paths: int = Field(default=60, ge=20, le=200)
    block_size: int = Field(default=8, ge=1, le=64)
    repeats: int = Field(default=3, ge=1, le=5)
    seed: int = Field(default=42, ge=0, le=2_147_483_647)

    @model_validator(mode="after")
    def validate_comparison(self) -> "ComparisonSettings":
        if len(set(self.models)) != len(self.models):
            raise ValueError("Comparison models must be unique.")
        if self.block_size > self.lookback // 2:
            raise ValueError("Block size must be no more than half of the lookback window.")
        return self
