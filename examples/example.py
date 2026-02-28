from kiteconnect import KiteConnect
import pandas as pd
from zerodha_talib import HistoricalClient, add_basics, add_talib

# Display settings
pd.set_option('display.max_rows', 100000)
pd.set_option('display.max_columns', 50)
pd.set_option('display.width', None)

# API credentials
api_key = 'your api key'
access_token = 'your access token'

kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

client = HistoricalClient(kite)

# 1) Fetch historical candles only
df = client.fetch(
    instrument_name='NIFTY 50',
    exchange='NSE',
    from_date='2010-01-01',
    to_date='2026-02-28',
    interval='day',
)

print('Raw OHLCV:')
print(df.tail(5))

# 2) add_basics + add_talib (nubra_talib style)
#df = add_basics(df)
df_ta = add_talib(
    df,
    funcs={
        "RSI": {"timeperiod": 14},
        "EMA": {"timeperiod": 21},
        "CCI": {"timeperiod": 14},
        "MACD": {"fastperiod": 12, "slowperiod": 26, "signalperiod": 9},
    },
)

print('\nWith indicators (add_talib):')
print(df_ta.tail(5))
