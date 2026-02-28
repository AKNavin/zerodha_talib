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
from zerodha_talib import HistoricalClient, add_basics, add_talib

kite = KiteConnect(api_key="YOUR_API_KEY")
kite.set_access_token("YOUR_ACCESS_TOKEN")

client = HistoricalClient(kite)

df = client.fetch(
    instrument_name="NIFTY 50",
    exchange="NSE",
    from_date="2010-01-01",
    to_date="2026-02-28",
    interval="day",
)

# Default basics: SMA_9, EMA_21, RSI_14
df = add_basics(df)

# nubra_talib-style explicit call
df = add_talib(
    df,
    funcs={
        "RSI": {"timeperiod": 14},
        "EMA": {"timeperiod": 21},
        "SMA": {"timeperiod": 9},
        # "MACD": {"fastperiod": 12, "slowperiod": 26, "signalperiod": 9},
    },
)

print(df.tail())
```

## Example Script

```bash
set ZERODHA_API_KEY=your_api_key
python examples/example.py
```

`examples/example.py` reads `ZERODHA_ACCESS_TOKEN` from env, or falls back to:
`C:\Trading\OptionAnalysis\AccessToken.txt`

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
