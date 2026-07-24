from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

import pandas as pd

from app.core.schemas import ConnectorRequest
from app.services.data_service import DataReport, normalise_market_data

_MAX_RESPONSE_BYTES = 5 * 1024 * 1024


@dataclass(frozen=True)
class ConnectorInfo:
    id: str
    name: str
    public: bool
    maximum_candles: int
    intervals: tuple[str, ...]
    symbol_example: str
    note: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "public": self.public,
            "maximum_candles": self.maximum_candles,
            "intervals": list(self.intervals),
            "symbol_example": self.symbol_example,
            "note": self.note,
        }


CONNECTORS = {
    "binance": ConnectorInfo(
        id="binance",
        name="Binance Spot market data",
        public=True,
        maximum_candles=1000,
        intervals=("1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"),
        symbol_example="BTCUSDT",
        note="Uses Binance's public market-data-only Kline endpoint; availability depends on region and provider uptime.",
    ),
    "coinbase": ConnectorInfo(
        id="coinbase",
        name="Coinbase Exchange market data",
        public=True,
        maximum_candles=300,
        intervals=("1m", "5m", "15m", "1h", "6h", "1d"),
        symbol_example="BTC-USD",
        note="Uses the public Coinbase Exchange historic-rates endpoint; requests are limited to 300 buckets.",
    ),
    "kraken": ConnectorInfo(
        id="kraken",
        name="Kraken Spot market data",
        public=True,
        maximum_candles=720,
        intervals=("1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"),
        symbol_example="XBTUSD",
        note="Uses Kraken's public OHLC endpoint, which returns up to 720 recent entries.",
    ),
}

_BINANCE_INTERVALS = {value: value for value in CONNECTORS["binance"].intervals}
_COINBASE_INTERVALS = {"1m": 60, "5m": 300, "15m": 900, "1h": 3600, "6h": 21600, "1d": 86400}
_KRAKEN_INTERVALS = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240, "1d": 1440, "1w": 10080}


def list_connectors() -> list[dict[str, Any]]:
    return [connector.as_dict() for connector in CONNECTORS.values()]


def _fetch_json(url: str) -> Any:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "MarketForge-AI/0.5 (+https://github.com/bryanssss/marketforge-ai)",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=15) as response:  # noqa: S310 - fixed trusted hosts
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > _MAX_RESPONSE_BYTES:
            raise ValueError("The exchange response is unexpectedly large.")
        body = response.read(_MAX_RESPONSE_BYTES + 1)
        if len(body) > _MAX_RESPONSE_BYTES:
            raise ValueError("The exchange response exceeded the safety limit.")
    return json.loads(body.decode("utf-8"))


def _binance(request: ConnectorRequest, fetcher: Callable[[str], Any]) -> pd.DataFrame:
    interval = _BINANCE_INTERVALS.get(request.interval)
    if interval is None:
        raise ValueError("Unsupported Binance interval.")
    symbol = request.symbol.replace("-", "").replace("/", "").replace("_", "").upper()
    query = urllib.parse.urlencode({"symbol": symbol, "interval": interval, "limit": min(request.limit, 1000)})
    payload = fetcher(f"https://data-api.binance.vision/api/v3/klines?{query}")
    if isinstance(payload, dict) and "msg" in payload:
        raise ValueError(f"Binance rejected the request: {payload['msg']}")
    rows = []
    for item in payload:
        rows.append(
            {
                "timestamp": pd.to_datetime(int(item[0]), unit="ms", utc=True),
                "open": item[1],
                "high": item[2],
                "low": item[3],
                "close": item[4],
                "volume": item[5],
                "amount": item[7],
            }
        )
    return pd.DataFrame(rows)


def _coinbase(request: ConnectorRequest, fetcher: Callable[[str], Any]) -> pd.DataFrame:
    granularity = _COINBASE_INTERVALS.get(request.interval)
    if granularity is None:
        raise ValueError("Unsupported Coinbase interval.")
    symbol = request.symbol.replace("/", "-").replace("_", "-").upper()
    query = urllib.parse.urlencode({"granularity": granularity})
    encoded_symbol = urllib.parse.quote(symbol, safe="-")
    payload = fetcher(f"https://api.exchange.coinbase.com/products/{encoded_symbol}/candles?{query}")
    if isinstance(payload, dict) and "message" in payload:
        raise ValueError(f"Coinbase rejected the request: {payload['message']}")
    rows = []
    for item in payload[: min(request.limit, 300)]:
        rows.append(
            {
                "timestamp": pd.to_datetime(int(item[0]), unit="s", utc=True),
                "low": item[1],
                "high": item[2],
                "open": item[3],
                "close": item[4],
                "volume": item[5] if len(item) > 5 else 0.0,
            }
        )
    return pd.DataFrame(rows)


def _kraken(request: ConnectorRequest, fetcher: Callable[[str], Any]) -> pd.DataFrame:
    interval = _KRAKEN_INTERVALS.get(request.interval)
    if interval is None:
        raise ValueError("Unsupported Kraken interval.")
    symbol = request.symbol.replace("-", "").replace("/", "").replace("_", "").upper()
    query = urllib.parse.urlencode({"pair": symbol, "interval": interval})
    payload = fetcher(f"https://api.kraken.com/0/public/OHLC?{query}")
    errors = payload.get("error", []) if isinstance(payload, dict) else []
    if errors:
        raise ValueError("Kraken rejected the request: " + "; ".join(str(item) for item in errors))
    result = payload.get("result", {})
    pair_keys = [key for key in result if key != "last"]
    if not pair_keys:
        raise ValueError("Kraken returned no candles for that symbol.")
    rows = []
    for item in result[pair_keys[0]][-min(request.limit, 720) :]:
        rows.append(
            {
                "timestamp": pd.to_datetime(int(float(item[0])), unit="s", utc=True),
                "open": item[1],
                "high": item[2],
                "low": item[3],
                "close": item[4],
                "volume": item[6],
            }
        )
    return pd.DataFrame(rows)


def import_market_data(
    request: ConnectorRequest, fetcher: Callable[[str], Any] = _fetch_json
) -> tuple[pd.DataFrame, DataReport, dict[str, Any]]:
    connector = CONNECTORS.get(request.exchange)
    if connector is None:
        raise ValueError("Unknown exchange connector.")
    if request.exchange == "binance":
        raw = _binance(request, fetcher)
    elif request.exchange == "coinbase":
        raw = _coinbase(request, fetcher)
    else:
        raw = _kraken(request, fetcher)
    if raw.empty:
        raise ValueError("The exchange returned no market data.")
    normalised, report = normalise_market_data(raw)
    metadata = {
        "connector": connector.as_dict(),
        "symbol": request.symbol,
        "interval": request.interval,
        "requested_limit": request.limit,
        "received_rows": len(normalised),
    }
    return normalised, report, metadata
