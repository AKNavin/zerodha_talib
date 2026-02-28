"""TA helpers with a nubra_talib-like API."""

from __future__ import annotations

from typing import Any, Dict, Mapping

import pandas as pd


def add_basics(data: pd.DataFrame) -> pd.DataFrame:
    """Add a minimal default indicator set: SMA_9, EMA_21, RSI_14."""
    required = {"close"}
    missing = [col for col in required if col not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns for add_basics: {missing}")

    out = data.copy()
    close = _series(out, "close")
    out["SMA_9"] = close.rolling(window=9, min_periods=9).mean()
    out["EMA_21"] = close.ewm(span=21, adjust=False).mean()
    out["RSI_14"] = _rsi(close, period=14)
    return out


def add_talib(
    data: pd.DataFrame,
    funcs: Mapping[str, Mapping[str, Any]],
) -> pd.DataFrame:
    """Add TA-Lib style indicators from a function config map.

    Example:
        add_talib(df, funcs={"RSI": {"timeperiod": 14}, "EMA": {"timeperiod": 21}})
    """
    out = data.copy()

    for name, params in funcs.items():
        fn = name.upper()
        cfg = dict(params or {})

        if fn == "SMA":
            period = int(cfg.get("timeperiod", 20))
            close_col = cfg.get("price", "close")
            close = _series(out, close_col)
            out[f"SMA_{period}"] = close.rolling(window=period, min_periods=period).mean()
        elif fn == "EMA":
            period = int(cfg.get("timeperiod", 20))
            close_col = cfg.get("price", "close")
            close = _series(out, close_col)
            out[f"EMA_{period}"] = close.ewm(span=period, adjust=False).mean()
        elif fn == "RSI":
            period = int(cfg.get("timeperiod", 14))
            close_col = cfg.get("price", "close")
            close = _series(out, close_col)
            out[f"RSI_{period}"] = _rsi(close, period=period)
        elif fn == "CCI":
            period = int(cfg.get("timeperiod", 14))
            high_col = cfg.get("high", "high")
            low_col = cfg.get("low", "low")
            close_col = cfg.get("close", "close")
            high = _series(out, high_col)
            low = _series(out, low_col)
            close = _series(out, close_col)
            out[f"CCI_{period}"] = _cci(high, low, close, period=period)
        elif fn == "MACD":
            fast = int(cfg.get("fastperiod", 12))
            slow = int(cfg.get("slowperiod", 26))
            signal = int(cfg.get("signalperiod", 9))
            close_col = cfg.get("price", "close")
            close = _series(out, close_col)
            fast_ema = close.ewm(span=fast, adjust=False).mean()
            slow_ema = close.ewm(span=slow, adjust=False).mean()
            out["MACD"] = fast_ema - slow_ema
            out["MACD_SIGNAL"] = out["MACD"].ewm(span=signal, adjust=False).mean()
            out["MACD_HIST"] = out["MACD"] - out["MACD_SIGNAL"]
        elif fn == "BBANDS":
            period = int(cfg.get("timeperiod", 20))
            std = float(cfg.get("nbdev", 2.0))
            close_col = cfg.get("price", "close")
            close = _series(out, close_col)
            mid = close.rolling(window=period, min_periods=period).mean()
            sigma = close.rolling(window=period, min_periods=period).std(ddof=0)
            out[f"BB_MIDDLE_{period}"] = mid
            out[f"BB_UPPER_{period}"] = mid + std * sigma
            out[f"BB_LOWER_{period}"] = mid - std * sigma
        else:
            raise ValueError(f"Unsupported indicator: {name}")

    return out


def _series(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        raise ValueError(f"Missing required column: {col}")
    return pd.to_numeric(df[col], errors="coerce")


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    return 100 - (100 / (1 + rs))


def _cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    tp = (high + low + close) / 3.0
    sma = tp.rolling(window=period, min_periods=period).mean()
    mad = tp.rolling(window=period, min_periods=period).apply(
        lambda x: (x - x.mean()).abs().mean(), raw=False
    )
    return (tp - sma) / (0.015 * mad.replace(0, pd.NA))
