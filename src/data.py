"""
Data layer for Phase 1.

IMPORTANT — READ THIS:
This sandbox environment has no outbound network access to market data
providers (Yahoo Finance, Binance, etc. are blocked by organization egress
policy). `fetch_ohlcv()` below is written as the real interface you'd wire a
live data source into, but it currently raises NotImplementedError.

For the Phase 1 mechanical dry run, we use `generate_synthetic_ohlcv()`
instead — clearly-labeled, seeded, fake price data. This is fine because
Phase 1's entire purpose is to prove the pipeline's plumbing (ordering,
logging immutability, no-lookahead, benchmark math), which does not require
real prices. Every output produced from synthetic data is tagged
`data_source="SYNTHETIC"` so it can never be mistaken for a real result.

Before Phase 2 (forward paper trading, the actual evidence-gathering phase),
`fetch_ohlcv()` must be implemented against a real source (e.g. yfinance or
an exchange API via ccxt) from an environment that can reach it.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


def fetch_ohlcv(ticker: str, lookback_days: int, interval: str) -> pd.DataFrame:
    """Real data fetch — not available in this sandbox. Wire this up to a
    live source (yfinance, ccxt, etc.) before running Phase 2."""
    raise NotImplementedError(
        "No outbound network access to market data providers in this "
        "environment. Use generate_synthetic_ohlcv() for the Phase 1 dry "
        "run, and implement this function against a real data source "
        "before any Phase 2 (paper trading) run."
    )


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
