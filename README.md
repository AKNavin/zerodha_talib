# zerodha_talib

Zerodha historical data to pandas with TA-Lib indicators.

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-success)

- GitHub: https://github.com/AKNavin/zerodha_talib

## Install

```bash
pip install zerodha-talib
```

For local development:

```bash
pip install -e .[dev]
```

## Usage

```python
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
```

## Example Script

```bash
python examples/example.py
```

## Historical Fetch Defaults

- `batch_days=2000`
- `throttle_seconds=0.5`
- `retries=3`
- `backoff_seconds=1.0`

## API

- `HistoricalClient(kite)`
- `HistoricalClient.fetch(...)`
- `add_basics(df)` -> adds `SMA_9`, `EMA_21`, `RSI_14`
- `add_talib(df, funcs={...})`

## Release Checklist

- [ ] Update version in `pyproject.toml`
- [ ] Validate imports with `pip install -e .`
- [ ] Run your sample script: `python examples/example.py`
- [ ] Run tests (if using dev deps): `pytest`
- [ ] Build artifacts: `python -m build`
- [ ] Check artifacts in `dist/`
- [ ] Commit + tag release in Git
- [ ] Push to GitHub

## License

MIT
