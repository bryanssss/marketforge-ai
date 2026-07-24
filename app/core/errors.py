class MarketForgeError(Exception):
    """Base exception for errors safe to show to the user."""


class DataValidationError(MarketForgeError):
    """Raised when uploaded market data cannot be safely analysed."""


class ForecastError(MarketForgeError):
    """Raised when a forecasting engine cannot complete a request."""
