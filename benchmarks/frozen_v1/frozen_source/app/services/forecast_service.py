from __future__ import annotations

import importlib
import sys
import threading
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from app.core.config import KRONOS_DIR
from app.core.errors import ForecastError
from app.core.schemas import ForecastSettings
from app.services.data_service import infer_step, rows_for_json

_EPSILON = np.finfo(float).eps
_MODEL_CACHE: dict[tuple[str, str, str | None, str | None], "_KronosRuntime"] = {}
_MODEL_CACHE_LOCK = threading.Lock()


@dataclass
class ForecastResult:
    engine: str
    history: pd.DataFrame
    forecast: pd.DataFrame
    summary: dict[str, Any]
    notes: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)
    fallback: dict[str, str] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "engine": self.engine,
            "history": rows_for_json(self.history),
            "forecast": rows_for_json(self.forecast),
            "summary": self.summary,
            "notes": self.notes,
            "metadata": self.metadata,
            "fallback": self.fallback,
        }


@dataclass
class _KronosRuntime:
    predictor: Any
    model_id: str
    tokenizer_id: str
    device: str
    model_revision: str | None = None
    tokenizer_revision: str | None = None
    lock: threading.Lock = field(default_factory=threading.Lock)


def kronos_available() -> bool:
    return (KRONOS_DIR / "model" / "__init__.py").exists()


def kronos_status() -> dict[str, Any]:
    return {
        "installed": kronos_available(),
        "path": str(KRONOS_DIR),
        "cached_models": [
            f"{size}:{device}:{model_revision or 'main'}:{tokenizer_revision or 'main'}"
            for size, device, model_revision, tokenizer_revision in _MODEL_CACHE
        ],
        "research_warning": (
            "The public pretraining cut-off is not clearly documented. Do not claim clean out-of-sample "
            "Kronos results without a verified model training cut-off."
        ),
    }


def _future_timestamps(context: pd.DataFrame, horizon: int) -> pd.DatetimeIndex:
    step = infer_step(context)
    return pd.date_range(context["timestamp"].iloc[-1] + step, periods=horizon, freq=step)


def _historical_features(context: pd.DataFrame) -> dict[str, np.ndarray]:
    previous_close = context["close"].shift(1)
    valid = previous_close.notna()
    previous = previous_close[valid].to_numpy(dtype=float)
    opens = context.loc[valid, "open"].to_numpy(dtype=float)
    closes = context.loc[valid, "close"].to_numpy(dtype=float)
    highs = context.loc[valid, "high"].to_numpy(dtype=float)
    lows = context.loc[valid, "low"].to_numpy(dtype=float)

    gap = np.log(np.maximum(opens, _EPSILON) / np.maximum(previous, _EPSILON))
    body = np.log(np.maximum(closes, _EPSILON) / np.maximum(opens, _EPSILON))
    close_return = gap + body
    upper_wick = np.maximum(highs / np.maximum(np.maximum(opens, closes), _EPSILON) - 1.0, 0.0)
    lower_wick = np.maximum(1.0 - lows / np.maximum(np.minimum(opens, closes), _EPSILON), 0.0)
    log_volume = np.log1p(context.loc[valid, "volume"].to_numpy(dtype=float))

    features = {
        "gap": np.nan_to_num(gap, nan=0.0, posinf=0.0, neginf=0.0),
        "body": np.nan_to_num(body, nan=0.0, posinf=0.0, neginf=0.0),
        "return": np.nan_to_num(close_return, nan=0.0, posinf=0.0, neginf=0.0),
        "upper_wick": np.clip(np.nan_to_num(upper_wick), 0.0, 2.0),
        "lower_wick": np.clip(np.nan_to_num(lower_wick), 0.0, 0.999999),
        "log_volume": np.clip(np.nan_to_num(log_volume), 0.0, 50.0),
    }
    if "amount" in context.columns:
        features["log_amount"] = np.clip(
            np.nan_to_num(np.log1p(context.loc[valid, "amount"].to_numpy(dtype=float))),
            0.0,
            60.0,
        )
    return features


def _sample_block_indices(
    history_length: int,
    paths: int,
    horizon: int,
    block_size: int,
    rng: np.random.Generator,
) -> np.ndarray:
    if history_length < 2:
        raise ForecastError("Not enough price changes to create a forecast.")
    block_size = max(1, min(block_size, history_length))
    output = np.empty((paths, horizon), dtype=np.int64)
    for path in range(paths):
        position = 0
        while position < horizon:
            start = int(rng.integers(0, history_length - block_size + 1))
            take = min(block_size, horizon - position)
            output[path, position : position + take] = np.arange(start, start + take)
            position += take
    return output


def _robust_regime_stats(returns: np.ndarray) -> tuple[float, float]:
    recent = returns[-min(128, len(returns)) :]
    median = float(np.median(recent))
    mean = float(np.mean(recent))
    drift = float(np.clip(0.70 * median + 0.30 * mean, -0.02, 0.02)) * 0.25
    mad = float(np.median(np.abs(recent - np.median(recent))))
    robust_sigma = 1.4826 * mad
    standard_sigma = float(np.std(recent, ddof=1)) if len(recent) > 1 else 0.0
    volatility = max(robust_sigma, standard_sigma * 0.5, 1e-6)
    return drift, volatility


def _paths_from_features(
    context: pd.DataFrame,
    settings: ForecastSettings,
    model: str,
) -> dict[str, np.ndarray]:
    features = _historical_features(context)
    historical_returns = features["return"]
    drift, volatility = _robust_regime_stats(historical_returns)
    rng = np.random.default_rng(settings.seed)
    paths = settings.paths
    horizon = settings.horizon

    if model == "ensemble":
        block_count = max(1, paths // 2)
        drift_count = max(1, paths // 3)
        naive_count = max(1, paths - block_count - drift_count)
        parts = [
            _paths_from_features(
                context,
                settings.model_copy(update={"paths": block_count, "seed": settings.seed + 11}),
                "block_bootstrap",
            ),
            _paths_from_features(
                context,
                settings.model_copy(update={"paths": drift_count, "seed": settings.seed + 29}),
                "drift",
            ),
            _paths_from_features(
                context,
                settings.model_copy(update={"paths": naive_count, "seed": settings.seed + 47}),
                "naive",
            ),
        ]
        return {
            key: np.concatenate([part[key] for part in parts], axis=0)
            for key in parts[0]
        }

    history_length = len(historical_returns)
    indices = _sample_block_indices(
        history_length,
        paths,
        horizon,
        settings.block_size if model == "block_bootstrap" else 1,
        rng,
    )

    sampled_gap = features["gap"][indices]
    sampled_body = features["body"][indices]
    if model == "block_bootstrap":
        historical_mean = float(np.mean(historical_returns))
        adjustment = drift - historical_mean * 0.25
        sampled_body = sampled_body + adjustment
    elif model == "drift":
        shocks = rng.normal(0.0, volatility, size=(paths, horizon))
        sampled_gap = sampled_gap * 0.15
        sampled_body = drift + shocks - sampled_gap
    elif model == "naive":
        shocks = rng.normal(0.0, volatility * 0.35, size=(paths, horizon))
        sampled_gap = sampled_gap * 0.05
        sampled_body = shocks - sampled_gap
    else:
        raise ForecastError(f"Unknown baseline model: {model}")

    upper_wick = features["upper_wick"][indices]
    lower_wick = features["lower_wick"][indices]
    log_volume = features["log_volume"][indices]
    log_amount = features.get("log_amount")
    sampled_log_amount = log_amount[indices] if log_amount is not None else None

    opens = np.empty((paths, horizon), dtype=float)
    highs = np.empty_like(opens)
    lows = np.empty_like(opens)
    closes = np.empty_like(opens)
    volumes = np.empty_like(opens)
    amounts = np.empty_like(opens) if sampled_log_amount is not None else None

    previous_close = np.full(paths, float(context["close"].iloc[-1]), dtype=float)
    for step in range(horizon):
        open_values = previous_close * np.exp(np.clip(sampled_gap[:, step], -0.25, 0.25))
        close_values = open_values * np.exp(np.clip(sampled_body[:, step], -0.35, 0.35))
        high_values = np.maximum(open_values, close_values) * (1.0 + upper_wick[:, step])
        low_values = np.minimum(open_values, close_values) * (1.0 - lower_wick[:, step])

        opens[:, step] = np.maximum(open_values, _EPSILON)
        closes[:, step] = np.maximum(close_values, _EPSILON)
        highs[:, step] = np.maximum(high_values, np.maximum(opens[:, step], closes[:, step]))
        lows[:, step] = np.maximum(
            np.minimum(low_values, np.minimum(opens[:, step], closes[:, step])),
            _EPSILON,
        )
        volumes[:, step] = np.maximum(np.expm1(log_volume[:, step]), 0.0)
        if amounts is not None and sampled_log_amount is not None:
            amounts[:, step] = np.maximum(np.expm1(sampled_log_amount[:, step]), 0.0)
        previous_close = closes[:, step]

    result = {
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volumes,
    }
    if amounts is not None:
        result["amount"] = amounts
    return result


def _quantile_forecast(
    path_values: dict[str, np.ndarray],
    timestamps: pd.DatetimeIndex,
) -> pd.DataFrame:
    forecast = pd.DataFrame({"timestamp": timestamps})
    for name in ("open", "high", "low", "close", "volume", "amount"):
        if name in path_values:
            forecast[name] = np.median(path_values[name], axis=0)

    close_paths = path_values["close"]
    for quantile, label in (
        (0.05, "q05_close"),
        (0.10, "lower_close"),
        (0.25, "q25_close"),
        (0.50, "q50_close"),
        (0.75, "q75_close"),
        (0.90, "upper_close"),
        (0.95, "q95_close"),
    ):
        forecast[label] = np.quantile(close_paths, quantile, axis=0)

    forecast["high"] = forecast[["open", "close", "high"]].max(axis=1)
    forecast["low"] = forecast[["open", "close", "low"]].min(axis=1).clip(lower=_EPSILON)
    forecast["volume"] = forecast["volume"].clip(lower=0)
    if "amount" in forecast:
        forecast["amount"] = forecast["amount"].clip(lower=0)
    return forecast


def baseline_forecast(df: pd.DataFrame, settings: ForecastSettings) -> ForecastResult:
    context = df.tail(min(settings.lookback, len(df))).copy()
    if len(context) < 40:
        raise ForecastError("At least 40 candles are required for forecasting.")

    path_values = _paths_from_features(context, settings, settings.baseline_model)
    timestamps = _future_timestamps(context, settings.horizon)
    forecast = _quantile_forecast(path_values, timestamps)

    last_close = float(context["close"].iloc[-1])
    median_close = float(forecast["close"].iloc[-1])
    historical_returns = np.diff(np.log(context["close"].to_numpy(dtype=float)))
    _, volatility = _robust_regime_stats(historical_returns)
    expected_return = (median_close / last_close - 1.0) * 100
    interval_width = (
        float(forecast["upper_close"].iloc[-1]) / max(float(forecast["lower_close"].iloc[-1]), _EPSILON) - 1.0
    ) * 100

    summary = {
        "last_close": round(last_close, 8),
        "forecast_close": round(median_close, 8),
        "expected_return_percent": round(expected_return, 3),
        "lower_close": round(float(forecast["lower_close"].iloc[-1]), 8),
        "upper_close": round(float(forecast["upper_close"].iloc[-1]), 8),
        "interval_width_percent": round(interval_width, 3),
        "estimated_volatility_percent": round(volatility * 100, 3),
        "paths": int(path_values["close"].shape[0]),
        "horizon": settings.horizon,
        "baseline_model": settings.baseline_model,
    }
    notes = [
        "The baseline produces a distribution of possible paths, not one guaranteed future line.",
        "Moving-block sampling preserves short runs of candle behaviour better than independent random returns.",
        "The 80% range should be checked for calibration with walk-forward tests on each market and timeframe.",
        "Research and education only; not financial advice.",
    ]
    return ForecastResult(
        engine=f"baseline-{settings.baseline_model}",
        history=context.tail(400),
        forecast=forecast,
        summary=summary,
        notes=notes,
        metadata={
            "algorithm": settings.baseline_model,
            "seed": settings.seed,
            "lookback": len(context),
            "block_size": settings.block_size,
            "interval": "80% central interval",
            "reproducible": True,
        },
    )


def _resolve_device(requested: str) -> str | None:
    return None if requested == "auto" else requested


def _load_kronos_runtime(
    model_size: str,
    device: str,
    model_revision: str | None = None,
    tokenizer_revision: str | None = None,
) -> _KronosRuntime:
    cache_key = (model_size, device, model_revision, tokenizer_revision)
    with _MODEL_CACHE_LOCK:
        cached = _MODEL_CACHE.get(cache_key)
        if cached is not None:
            return cached

        if not kronos_available():
            raise ForecastError(
                "Kronos is not installed. Run the included installation script, then restart MarketForge AI."
            )

        kronos_root = str(KRONOS_DIR)
        if kronos_root not in sys.path:
            sys.path.insert(0, kronos_root)
        try:
            module = importlib.import_module("model")
            Kronos = getattr(module, "Kronos")
            KronosTokenizer = getattr(module, "KronosTokenizer")
            KronosPredictor = getattr(module, "KronosPredictor")
        except Exception as exc:
            raise ForecastError("The installed Kronos source could not be imported.") from exc

        model_map = {
            "mini": ("NeoQuasar/Kronos-mini", "NeoQuasar/Kronos-Tokenizer-2k", 2048),
            "small": ("NeoQuasar/Kronos-small", "NeoQuasar/Kronos-Tokenizer-base", 512),
            "base": ("NeoQuasar/Kronos-base", "NeoQuasar/Kronos-Tokenizer-base", 512),
        }
        model_id, tokenizer_id, max_context = model_map[model_size]
        try:
            tokenizer_kwargs = {"revision": tokenizer_revision} if tokenizer_revision else {}
            model_kwargs = {"revision": model_revision} if model_revision else {}
            tokenizer = KronosTokenizer.from_pretrained(tokenizer_id, **tokenizer_kwargs)
            model = Kronos.from_pretrained(model_id, **model_kwargs)
            tokenizer.eval()
            model.eval()
            predictor = KronosPredictor(
                model,
                tokenizer,
                device=_resolve_device(device),
                max_context=max_context,
            )
        except Exception as exc:
            raise ForecastError(
                "Kronos or its model weights could not be loaded. Check the installation, internet access and available memory."
            ) from exc

        runtime = _KronosRuntime(
            predictor=predictor,
            model_id=model_id,
            tokenizer_id=tokenizer_id,
            device=str(getattr(predictor, "device", device)),
            model_revision=model_revision,
            tokenizer_revision=tokenizer_revision,
        )
        _MODEL_CACHE[cache_key] = runtime
        return runtime


def _validate_kronos_prediction(prediction: pd.DataFrame, timestamps: pd.DatetimeIndex) -> pd.DataFrame:
    output = prediction.copy().reset_index(drop=True)
    output["timestamp"] = timestamps
    for column in ("open", "high", "low", "close"):
        if column not in output:
            raise ForecastError(f"Kronos did not return the required {column} column.")
        output[column] = pd.to_numeric(output[column], errors="coerce")
    if output[["open", "high", "low", "close"]].isna().any().any():
        raise ForecastError("Kronos returned invalid price values.")
    output[["open", "high", "low", "close"]] = output[["open", "high", "low", "close"]].clip(
        lower=_EPSILON
    )
    output["volume"] = pd.to_numeric(output.get("volume", 0.0), errors="coerce").fillna(0).clip(lower=0)
    if "amount" in output:
        output["amount"] = pd.to_numeric(output["amount"], errors="coerce").fillna(0).clip(lower=0)
    output["high"] = output[["open", "high", "close"]].max(axis=1)
    output["low"] = output[["open", "low", "close"]].min(axis=1).clip(lower=_EPSILON)
    return output


def kronos_forecast(df: pd.DataFrame, settings: ForecastSettings) -> ForecastResult:
    runtime = _load_kronos_runtime(
        settings.model_size,
        settings.device,
        settings.model_revision,
        settings.tokenizer_revision,
    )
    max_context = 2048 if settings.model_size == "mini" else 512
    context = df.tail(min(settings.lookback, max_context)).copy()
    timestamps = _future_timestamps(context, settings.horizon)
    future_times = pd.Series(timestamps)
    history_times = pd.Series(context["timestamp"].reset_index(drop=True))

    feature_columns = ["open", "high", "low", "close", "volume"]
    if "amount" in context.columns:
        feature_columns.append("amount")
    features = context[feature_columns].reset_index(drop=True)

    draws: list[pd.DataFrame] = []
    requested_draws = settings.kronos_samples
    try:
        import torch
    except Exception as exc:
        raise ForecastError("PyTorch is required for the Kronos engine.") from exc

    with runtime.lock:
        for draw_index in range(requested_draws):
            seed = settings.seed + draw_index
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed)
            try:
                with torch.inference_mode():
                    prediction = runtime.predictor.predict(
                        df=features,
                        x_timestamp=history_times,
                        y_timestamp=future_times,
                        pred_len=settings.horizon,
                        T=settings.temperature,
                        top_p=settings.top_p,
                        sample_count=1,
                        verbose=False,
                    )
            except Exception as exc:
                raise ForecastError("Kronos inference failed for this dataset and configuration.") from exc
            draws.append(_validate_kronos_prediction(prediction, timestamps))

    stacked: dict[str, np.ndarray] = {}
    for column in ("open", "high", "low", "close", "volume", "amount"):
        if column in draws[0]:
            stacked[column] = np.stack([draw[column].to_numpy(dtype=float) for draw in draws], axis=0)
    forecast = _quantile_forecast(stacked, timestamps)

    last_close = float(context["close"].iloc[-1])
    forecast_close = float(forecast["close"].iloc[-1])
    expected_return = (forecast_close / last_close - 1.0) * 100
    summary = {
        "last_close": round(last_close, 8),
        "forecast_close": round(forecast_close, 8),
        "expected_return_percent": round(expected_return, 3),
        "lower_close": round(float(forecast["lower_close"].iloc[-1]), 8),
        "upper_close": round(float(forecast["upper_close"].iloc[-1]), 8),
        "paths": requested_draws,
        "horizon": settings.horizon,
        "model": runtime.model_id,
        "device": runtime.device,
    }
    notes = [
        "Powered by the separately installed official Kronos model and public weights.",
        "MarketForge runs independent stochastic draws to show a forecast range instead of copying one line into both bounds.",
        "The public Kronos training cut-off is not clearly documented; treat historical evaluation as potentially contaminated unless verified.",
        "Research and education only; not financial advice.",
    ]
    return ForecastResult(
        engine=f"kronos-{settings.model_size}",
        history=context.tail(400),
        forecast=forecast,
        summary=summary,
        notes=notes,
        metadata={
            "model_id": runtime.model_id,
            "tokenizer_id": runtime.tokenizer_id,
            "model_revision": runtime.model_revision,
            "tokenizer_revision": runtime.tokenizer_revision,
            "device": runtime.device,
            "independent_draws": requested_draws,
            "model_cached": True,
            "oos_status": "unverified-training-cutoff",
        },
    )


def create_forecast(df: pd.DataFrame, settings: ForecastSettings) -> ForecastResult:
    if settings.engine == "kronos":
        return kronos_forecast(df, settings)
    if settings.engine == "auto" and kronos_available():
        try:
            return kronos_forecast(df, settings)
        except ForecastError as exc:
            fallback_settings = settings.model_copy(update={"engine": "baseline"})
            result = baseline_forecast(df, fallback_settings)
            result.fallback = {
                "from": "kronos",
                "to": result.engine,
                "reason": str(exc),
            }
            result.notes.insert(0, "Kronos could not complete this request, so an explicit baseline fallback was used.")
            return result
    return baseline_forecast(df, settings)
