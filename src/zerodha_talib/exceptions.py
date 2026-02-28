"""Custom exceptions for zerodha_talib."""


class InstrumentNotFoundError(ValueError):
    """Raised when no instrument is found for the provided name/exchange."""


class HistoricalFetchError(RuntimeError):
    """Raised when historical data could not be fetched after retries."""
