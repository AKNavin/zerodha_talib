"""Historical + TA client for Zerodha Kite API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import time
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

import pandas as pd

from .exceptions import HistoricalFetchError, InstrumentNotFoundError

DateLike = Union[str, date, datetime]


@dataclass
class RetryConfig:
    retries: int = 3
    backoff_seconds: float = 1.0


class HistoricalClient:
    """Fetch Zerodha historical data with automatic batching and TA helpers."""

    def __init__(
        self,
        kite: Any,
        batch_days: int = 2000,
        throttle_seconds: float = 0.5,
        retries: int = 3,
        backoff_seconds: float = 1.0,
    ) -> None:
        self.kite = kite
        self.batch_days = batch_days
        self.throttle_seconds = throttle_seconds
        self.retry = RetryConfig(retries=retries, backoff_seconds=backoff_seconds)
        self._instrument_cache: Dict[str, List[Dict[str, Any]]] = {}

    def fetch(
        self,
        instrument_name: str,
        from_date: DateLike,
        to_date: DateLike,
        interval: str,
        exchange: str = "NSE",
        continuous: bool = False,
        oi: bool = False,
    ) -> pd.DataFrame:
        token = self.resolve_instrument_token(instrument_name, exchange=exchange)
        return self.fetch_by_token(
            instrument_token=token,
            from_date=from_date,
            to_date=to_date,
            interval=interval,
            continuous=continuous,
            oi=oi,
        )

    def fetch_by_token(
        self,
        instrument_token: Union[int, str],
        from_date: DateLike,
        to_date: DateLike,
        interval: str,
        continuous: bool = False,
        oi: bool = False,
    ) -> pd.DataFrame:
        start = self._coerce_datetime(from_date)
        end = self._coerce_datetime(to_date)

        if start > end:
            raise ValueError("from_date must be <= to_date")

        frames: List[pd.DataFrame] = []
        for window_start, window_end in self._iter_date_windows(start, end):
            raw = self._historical_with_retry(
                instrument_token=instrument_token,
                from_date=window_start,
                to_date=window_end,
                interval=interval,
                continuous=continuous,
                oi=oi,
            )
            if raw:
                frames.append(pd.DataFrame(raw))

            if self.throttle_seconds > 0:
                time.sleep(self.throttle_seconds)

        if not frames:
            return pd.DataFrame()

        data = pd.concat(frames, ignore_index=True)
        if "date" in data.columns:
            data["date"] = pd.to_datetime(data["date"])
            data = data.sort_values("date").drop_duplicates(subset=["date"], keep="last")
            data = data.reset_index(drop=True)

        return data

    def resolve_instrument_token(self, instrument_name: str, exchange: str = "NSE") -> int:
        exchange_upper = exchange.upper()
        records = self._get_instruments(exchange_upper)

        target = instrument_name.strip().upper()
        matches = [
            r for r in records if str(r.get("tradingsymbol", "")).upper() == target
        ]
        if not matches:
            raise InstrumentNotFoundError(
                f"Instrument '{instrument_name}' not found on exchange '{exchange_upper}'."
            )

        token = matches[0].get("instrument_token")
        if token is None:
            raise InstrumentNotFoundError(
                f"Instrument '{instrument_name}' found but missing instrument_token."
            )
        return int(token)

    def _get_instruments(self, exchange: str) -> List[Dict[str, Any]]:
        if exchange not in self._instrument_cache:
            self._instrument_cache[exchange] = self.kite.instruments(exchange)
        return self._instrument_cache[exchange]

    def _historical_with_retry(self, **kwargs: Any) -> List[Dict[str, Any]]:
        last_error: Optional[Exception] = None

        for attempt in range(self.retry.retries + 1):
            try:
                return self.kite.historical_data(**kwargs)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt >= self.retry.retries:
                    break

                delay = self.retry.backoff_seconds * (2**attempt)
                time.sleep(delay)

        raise HistoricalFetchError(
            f"Historical fetch failed after {self.retry.retries + 1} attempts"
        ) from last_error

    def _iter_date_windows(
        self, start: datetime, end: datetime
    ) -> Iterable[Tuple[datetime, datetime]]:
        cursor = start
        delta = timedelta(days=self.batch_days)

        while cursor <= end:
            window_end = min(cursor + delta, end)
            yield cursor, window_end
            cursor = window_end + timedelta(days=1)

    @staticmethod
    def _coerce_datetime(value: DateLike) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time())
        return pd.to_datetime(value).to_pydatetime()
