# Third-Party Notices

## Kronos

MarketForge AI can optionally connect to the open-source **Kronos** financial foundation
model created by the Kronos authors:

- Repository: `https://github.com/shiyu-coder/Kronos`
- Project page: `https://shiyu-coder.github.io/Kronos/`
- Licence: MIT

Kronos is not included in this repository by default. When installed under
`vendor/Kronos`, its original copyright and licence terms remain applicable. MarketForge
AI does not claim ownership of the Kronos architecture, source, model names, tokenizer
or public weights.

## Public Market-Data Providers

MarketForge includes optional read-only adapters for public market data from:

- Binance Spot public market-data endpoints
- Coinbase Exchange public candles
- Kraken public OHLC data

The providers are not affiliated with or endorsed by MarketForge AI. Their APIs, data,
availability, rate limits, symbols, terms and licences remain under the providers'
control. MarketForge does not redistribute a permanent copy of their live API data in
this repository.

Users are responsible for checking provider terms before redistribution or commercial
use of downloaded data.

## Open-Source Dependencies

MarketForge uses Python and browser dependencies listed in `requirements*.txt` and
`pyproject.toml`, including FastAPI, Uvicorn, pandas, NumPy, Pydantic and optional
PyTorch/Hugging Face components. Each dependency remains under its own licence.

MarketForge AI's original interface, data pipeline, forecasting baselines, portfolio and
research services, backtesting workflow, packaging and documentation are licensed under
this repository's MIT licence.
