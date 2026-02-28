from datetime import datetime

import pandas as pd
import pytest

from zerodha_talib import HistoricalClient, add_basics, add_talib
from zerodha_talib.exceptions import HistoricalFetchError, InstrumentNotFoundError


class FakeKite:
    def __init__(self):
        self.calls = []
        self.failures_remaining = 0

    def instruments(self, exchange):
        return [
            {"tradingsymbol": "RELIANCE", "instrument_token": 738561},
            {"tradingsymbol": "INFY", "instrument_token": 408065},
        ]

    def historical_data(self, **kwargs):
        self.calls.append(kwargs)
        if self.failures_remaining > 0:
            self.failures_remaining -= 1
            raise RuntimeError("temporary failure")
        return [
            {
                "date": kwargs["from_date"],
                "open": 1,
                "high": 2,
                "low": 0,
                "close": 1,
                "volume": 100,
            }
        ]


def test_resolve_token_case_insensitive():
    client = HistoricalClient(FakeKite())
    assert client.resolve_instrument_token("reliance", exchange="nse") == 738561


def test_resolve_token_not_found():
    client = HistoricalClient(FakeKite())
    with pytest.raises(InstrumentNotFoundError):
        client.resolve_instrument_token("UNKNOWN", exchange="NSE")


def test_fetch_batches_by_window():
    kite = FakeKite()
    client = HistoricalClient(kite, batch_days=2, throttle_seconds=0)

    df = client.fetch_by_token(
        instrument_token=738561,
        from_date="2024-01-01",
        to_date="2024-01-06",
        interval="day",
    )

    assert not df.empty
    assert len(kite.calls) == 2
    assert kite.calls[0]["from_date"] == datetime(2024, 1, 1)
    assert kite.calls[0]["to_date"] == datetime(2024, 1, 3)
    assert kite.calls[1]["from_date"] == datetime(2024, 1, 4)
    assert kite.calls[1]["to_date"] == datetime(2024, 1, 6)


def test_retry_then_success():
    kite = FakeKite()
    kite.failures_remaining = 2
    client = HistoricalClient(kite, throttle_seconds=0, retries=3, backoff_seconds=0)

    df = client.fetch_by_token(
        instrument_token=738561,
        from_date="2024-01-01",
        to_date="2024-01-01",
        interval="day",
    )

    assert not df.empty
    assert len(kite.calls) == 3


def test_retry_exhausted():
    kite = FakeKite()
    kite.failures_remaining = 5
    client = HistoricalClient(kite, throttle_seconds=0, retries=2, backoff_seconds=0)

    with pytest.raises(HistoricalFetchError):
        client.fetch_by_token(
            instrument_token=738561,
            from_date="2024-01-01",
            to_date="2024-01-01",
            interval="day",
        )


def test_add_talib_nubra_style():
    df = pd.DataFrame(
        {
            "open": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            "high": [101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120],
            "low": [99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118],
            "close": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
        }
    )
    df = add_basics(df)
    out = add_talib(
        df,
        funcs={
            "RSI": {"timeperiod": 14},
            "EMA": {"timeperiod": 21},
            "CCI": {"timeperiod": 14},
            "MACD": {"fastperiod": 12, "slowperiod": 26, "signalperiod": 9},
        },
    )
    assert "RSI_14" in out.columns
    assert "EMA_21" in out.columns
    assert "CCI_14" in out.columns
    assert "MACD" in out.columns
    assert "MACD_SIGNAL" in out.columns
    assert "MACD_HIST" in out.columns
