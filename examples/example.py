from pathlib import Path
import os

import pandas as pd
from kiteconnect import KiteConnect

from zerodha_talib import HistoricalClient, add_basics, add_talib

pd.set_option("display.max_rows", 100000)
pd.set_option("display.max_columns", 50)
pd.set_option("display.width", None)


def load_access_token() -> str:
    env_token = os.getenv("ZERODHA_ACCESS_TOKEN", "").strip()
    if env_token:
        return env_token

    token_path = Path(r"C:\Trading\OptionAnalysis\AccessToken.txt")
    if token_path.exists():
        return token_path.read_text(encoding="utf-8").strip()

    raise RuntimeError(
        "Set ZERODHA_ACCESS_TOKEN or create C:\\Trading\\OptionAnalysis\\AccessToken.txt"
    )


def main() -> None:
    api_key = os.getenv("ZERODHA_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Set ZERODHA_API_KEY before running this example")

    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(load_access_token())

    client = HistoricalClient(kite)

    df = client.fetch(
        instrument_name="NIFTY 50",
        exchange="NSE",
        from_date="2010-01-01",
        to_date="2026-02-28",
        interval="day",
    )

    # Default minimal set from your requirement:
    # SMA_9, EMA_21, RSI_14
    df_basic = add_basics(df)

    # Optional nubra_talib-style explicit indicator call
    df_ta = add_talib(
        df_basic,
        funcs={
            "RSI": {"timeperiod": 14},
            "EMA": {"timeperiod": 21},
            "SMA": {"timeperiod": 9},
        },
    )

    print(df_ta[["date", "close", "SMA_9", "EMA_21", "RSI_14"]].tail())


if __name__ == "__main__":
    main()
