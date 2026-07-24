from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

BaselineModel = Literal[
    "block_bootstrap",
    "drift",
    "naive",
    "ensemble",
    "exponential_smoothing",
    "momentum",
    "mean_reversion",
    "regime_ensemble",
]
CalibrationMethod = Literal["none", "empirical", "conformal"]


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
    calibration: CalibrationMethod = "empirical"
    interval_level: float = Field(default=0.80, ge=0.50, le=0.99)

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
    calibration: CalibrationMethod = "empirical"

    @model_validator(mode="after")
    def validate_backtest(self) -> "BacktestSettings":
        if self.block_size > self.lookback // 2:
            raise ValueError("Block size must be no more than half of the lookback window.")
        return self


class ComparisonSettings(BaseModel):
    models: list[BaselineModel] = Field(
        default_factory=lambda: [
            "regime_ensemble",
            "ensemble",
            "block_bootstrap",
            "exponential_smoothing",
            "momentum",
            "mean_reversion",
            "drift",
            "naive",
        ],
        min_length=1,
        max_length=8,
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


class ConnectorRequest(BaseModel):
    exchange: Literal["binance", "coinbase", "kraken"]
    symbol: str = Field(min_length=3, max_length=30, pattern=r"^[A-Za-z0-9/_-]+$")
    interval: str = Field(default="1h", min_length=2, max_length=8)
    limit: int = Field(default=500, ge=40, le=1000)


class PortfolioSettings(BaseModel):
    allocation: Literal["equal", "inverse_volatility", "risk_parity", "minimum_variance"] = (
        "inverse_volatility"
    )
    rebalance_every: int = Field(default=24, ge=1, le=10_000)
    lookback: int = Field(default=120, ge=20, le=2000)
    fee_percent: float = Field(default=0.10, ge=0, le=5)
    initial_capital: float = Field(default=10_000, gt=0, le=1_000_000_000)
    max_weight_percent: float = Field(default=60, gt=0, le=100)
    min_weight_percent: float = Field(default=0, ge=0, le=50)
    target_volatility_percent: float | None = Field(default=None, gt=0, le=200)

    @model_validator(mode="after")
    def validate_weights(self) -> "PortfolioSettings":
        if self.min_weight_percent > self.max_weight_percent:
            raise ValueError("Minimum weight cannot exceed maximum weight.")
        return self


class VolatilitySettings(BaseModel):
    method: Literal["ewma", "parkinson", "garman_klass", "ensemble"] = "ensemble"
    horizon: int = Field(default=24, ge=1, le=240)
    lookback: int = Field(default=120, ge=20, le=2048)
    decay: float = Field(default=0.94, gt=0.50, lt=1.0)
    annualisation_periods: int = Field(default=365 * 24, ge=1, le=1_000_000)


class StressSettings(BaseModel):
    price_shock_percent: float = Field(default=-10.0, ge=-95, le=500)
    volatility_multiplier: float = Field(default=2.0, ge=0.1, le=10)
    liquidity_cost_percent: float = Field(default=0.25, ge=0, le=20)
    scenarios: int = Field(default=1000, ge=100, le=20_000)
    seed: int = Field(default=42, ge=0, le=2_147_483_647)


class ProjectPayload(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)
    settings: dict[str, Any] = Field(default_factory=dict)
    dataset_fingerprints: list[str] = Field(default_factory=list, max_length=50)
    language: str = Field(default="en", min_length=2, max_length=10)


class ExperimentPayload(BaseModel):
    project_id: int | None = Field(default=None, ge=1)
    name: str = Field(min_length=1, max_length=160)
    kind: Literal["forecast", "backtest", "comparison", "portfolio", "volatility", "stress"]
    dataset_fingerprint: str = Field(default="", max_length=64)
    settings: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list, max_length=20)


class ModelRecordPayload(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    family: str = Field(min_length=1, max_length=80)
    version: str = Field(min_length=1, max_length=80)
    source: str = Field(default="local", max_length=500)
    revision: str = Field(default="", max_length=128)
    checksum: str = Field(default="", max_length=128)
    metadata: dict[str, Any] = Field(default_factory=dict)
    active: bool = True


class ReportRequest(BaseModel):
    template: Literal["executive", "research", "risk", "model_card"] = "research"
    title: str = Field(default="MarketForge AI Report", min_length=1, max_length=160)
    result: dict[str, Any]
    include_raw_settings: bool = True
    format: Literal["markdown", "html"] = "markdown"


class ReplicationRequest(BaseModel):
    candidate_name: str = Field(default="candidate", min_length=1, max_length=120)
    comparator_name: str = Field(default="comparator", min_length=1, max_length=120)
    alpha: float = Field(default=0.05, gt=0, lt=0.5)
    bootstrap_samples: int = Field(default=2000, ge=200, le=20_000)
    block_size: int = Field(default=5, ge=1, le=100)
    seed: int = Field(default=42, ge=0, le=2_147_483_647)
