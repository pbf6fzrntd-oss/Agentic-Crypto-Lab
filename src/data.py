"""
Data layer.

Phase 1 used only `generate_synthetic_ohlcv()` — clearly-labeled, seeded,
fake price data — because this sandbox had no outbound network access to
market data providers, and because Phase 1's entire purpose was to prove
the pipeline's plumbing (ordering, logging immutability, no-lookahead,
benchmark math), which does not require real prices. Every output produced
from synthetic data is tagged `data_source="SYNTHETIC"` so it can never be
mistaken for a real result.

Phase 2 (forward paper trading) needs real prices, so `fetch_ohlcv()` below
is now implemented:
  - primary: yfinance (`Ticker.history`) — Yahoo Finance serves daily crypto
    OHLCV for BTC-USD/ETH-USD-style tickers with no API key, and "1d" (this
    project's only configured bar_interval) is fully supported.
  - fallback: ccxt against Coinbase's public market-data endpoints (also no
    API key) — used only if the yfinance call raises or returns no rows.
Every row returned is tagged `data_source` with which path actually served
it (e.g. "REAL:yfinance" or "REAL:ccxt:coinbase"), the same way Phase 1
tagged everything "SYNTHETIC" — so a Phase 2 journal row can always be
traced back to where its price came from.

KNOWN LIMITATION (as of the environment this was implemented in): the sandbox
session used to write this code has an organization egress policy that
blocks every market-data host tried while implementing this — Yahoo
Finance's endpoints and Coinbase's, Binance's, and Kraken's public APIs all
returned a 403 policy denial at the proxy layer. `fetch_ohlcv()` has NOT
been exercised against live data as a result — it is implemented from each
library's documented interface, covered by unit tests that mock the
HTTP/client layer, but not proven against a real response. Run it once
manually from an environment with real network access and sanity-check the
output before trusting it in the Phase 2 runner.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]

# Interval strings this project uses (config.py `bar_interval`) mapped to
# each provider's own interval/timeframe spelling. Both happen to already
# match for "1d"; the maps exist so a future intraday interval (e.g. "1h")
# is a one-line addition here, not a rewrite of fetch_ohlcv.
_YFINANCE_INTERVAL = {"1d": "1d", "1h": "1h"}
_CCXT_TIMEFRAME = {"1d": "1d", "1h": "1h"}


def fetch_ohlcv(ticker: str, lookback_days: int, interval: str) -> pd.DataFrame:
    """
    Fetch real OHLCV bars for `ticker` (e.g. "BTC-USD"), most recent
    `lookback_days` bars, at `interval`. Tries yfinance first, falls back to
    ccxt/Coinbase on failure. Raises RuntimeError if both fail — callers
    must not silently substitute synthetic data for a failed real fetch.
    """
    try:
        df = _fetch_ohlcv_yfinance(ticker, lookback_days, interval)
        if df is not None and not df.empty:
            return df
        last_error = RuntimeError(f"yfinance returned no rows for {ticker}")
    except Exception as exc:  # noqa: BLE001 — any failure falls through to ccxt
        last_error = exc

    try:
        df = _fetch_ohlcv_ccxt(ticker, lookback_days, interval)
        if df is not None and not df.empty:
            return df
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            f"fetch_ohlcv({ticker!r}): both yfinance and ccxt fallback failed. "
            f"yfinance error: {last_error!r}; ccxt error: {exc!r}"
        ) from exc

    raise RuntimeError(
        f"fetch_ohlcv({ticker!r}): yfinance returned no data and ccxt "
        f"fallback also returned no data. yfinance error: {last_error!r}"
    )


def _fetch_ohlcv_yfinance(ticker: str, lookback_days: int, interval: str) -> pd.DataFrame:
    import yfinance as yf

    yf_interval = _YFINANCE_INTERVAL.get(interval, interval)

    # Crypto trades every calendar day, not just business days, so fetch a
    # calendar-day window with a buffer for any provider gaps.
    end = pd.Timestamp.now(tz="UTC").normalize() + pd.Timedelta(days=1)
    start = end - pd.Timedelta(days=int(lookback_days * 1.2) + 10)

    hist = yf.Ticker(ticker).history(
        start=start.date().isoformat(),
        end=end.date().isoformat(),
        interval=yf_interval,
        auto_adjust=False,
    )
    if hist is None or hist.empty:
        return hist

    hist = hist[REQUIRED_COLUMNS].tail(lookback_days).copy()
    hist.index = pd.to_datetime(hist.index)
    if hist.index.tz is not None:
        hist.index = hist.index.tz_localize(None)
    hist.index.name = "Date"
    hist.attrs["ticker"] = ticker
    hist.attrs["data_source"] = "REAL:yfinance"
    return hist


def _fetch_ohlcv_ccxt(ticker: str, lookback_days: int, interval: str) -> pd.DataFrame:
    import ccxt

    timeframe = _CCXT_TIMEFRAME.get(interval, interval)
    # ccxt's unified symbol format is "BASE/QUOTE"; this project's tickers
    # are "BASE-QUOTE" (e.g. "BTC-USD").
    symbol = ticker.replace("-", "/")

    exchange = ccxt.coinbase()
    since = exchange.parse8601(
        (pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=int(lookback_days * 1.2) + 10))
        .strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=lookback_days + 20)
    if not bars:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    df = pd.DataFrame(bars, columns=["ts", "Open", "High", "Low", "Close", "Volume"])
    df["Date"] = pd.to_datetime(df["ts"], unit="ms")
    df = df.set_index("Date")[REQUIRED_COLUMNS].tail(lookback_days)
    df.attrs["ticker"] = ticker
    df.attrs["data_source"] = "REAL:ccxt:coinbase"
    return df


def generate_synthetic_ohlcv(
    ticker: str,
    n_bars: int,
    seed: int,
    start_price: float = 100.0,
    daily_vol: float = 0.03,
) -> pd.DataFrame:
    """
    Generate clearly-synthetic daily OHLCV data via a seeded random walk.

    This is NOT real market data and must never be interpreted as evidence
    about any real asset's behavior. It exists solely so Phase 1 can exercise
    the full pipeline (data -> thesis -> risk -> decision -> log -> review)
    without requiring network access.
    """
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=n_bars)

    log_returns = rng.normal(loc=0.0002, scale=daily_vol, size=n_bars)
    close = start_price * np.exp(np.cumsum(log_returns))

    # Build plausible O/H/L around each close using independent noise so
    # High >= max(Open, Close) and Low <= min(Open, Close) always hold.
    open_ = close * (1 + rng.normal(0, daily_vol * 0.3, size=n_bars))
    intraday_range = np.abs(rng.normal(0, daily_vol * 0.6, size=n_bars))
    high = np.maximum(open_, close) * (1 + intraday_range)
    low = np.minimum(open_, close) * (1 - intraday_range)
    volume = rng.uniform(1e6, 5e6, size=n_bars)

    df = pd.DataFrame(
        {
            "Open": open_,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": volume,
        },
        index=dates,
    )
    df.index.name = "Date"
    df.attrs["ticker"] = ticker
    df.attrs["data_source"] = "SYNTHETIC"
    return df


def validate_ohlcv(df: pd.DataFrame, ticker: str) -> list[str]:
    """Return a list of validation problems (empty list = passed)."""
    problems: list[str] = []

    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        problems.append(f"{ticker}: missing columns {sorted(missing_cols)}")
        return problems  # can't check further without the columns

    if df.index.duplicated().any():
        problems.append(f"{ticker}: duplicate dates in index")

    if not df.index.is_monotonic_increasing:
        problems.append(f"{ticker}: dates not sorted ascending")

    if (df[REQUIRED_COLUMNS[:4]] <= 0).any().any():
        problems.append(f"{ticker}: non-positive price values present")

    bad_hl = df["High"] < df[["Open", "Close"]].max(axis=1)
    if bad_hl.any():
        problems.append(f"{ticker}: {int(bad_hl.sum())} bars where High < max(Open, Close)")

    bad_lo = df["Low"] > df[["Open", "Close"]].min(axis=1)
    if bad_lo.any():
        problems.append(f"{ticker}: {int(bad_lo.sum())} bars where Low > min(Open, Close)")

    if df[REQUIRED_COLUMNS].isna().any().any():
        problems.append(f"{ticker}: NaN values present")

    return problems
