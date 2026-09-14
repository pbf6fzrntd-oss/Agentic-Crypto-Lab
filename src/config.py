"""
Frozen parameters for Phase 1 (mechanical dry run).

Do not tune these against results. See RESEARCH_SPEC.md for the rules this
project is bound by.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Config:
    # Fixed universe — the top 20 non-stablecoin cryptocurrencies by market
    # cap, chosen (like the original BTC/ETH pair) for data availability and
    # liquidity, not for any expected edge. Expanded from (BTC-USD, ETH-USD)
    # on 2026-09-14, BEFORE any Phase 2 outcome had completed (see
    # RESEARCH_SPEC.md's "Universe expansion" note for why that ordering
    # matters and how each symbol below was verified).
    #
    # UNI7083-USD is Yahoo Finance's disambiguated symbol for Uniswap (plain
    # "UNI-USD" returns no data); every other symbol here is Yahoo's default
    # spelling. Each was confirmed via this project's own fetch_ohlcv() to
    # return real, validate_ohlcv()-clean data before being added, and its
    # identity (longName) was checked to rule out a same-symbol collision
    # with an unrelated asset — that check caught and excluded "TON-USD"
    # (resolves to an unrelated "TON Token", not Toncoin) and "ARB-USD"
    # (resolves to "ARbit", not Arbitrum) during that verification; both
    # would have silently put the wrong asset in the universe.
    universe: tuple = (
        "BTC-USD", "ETH-USD", "XRP-USD", "BNB-USD", "SOL-USD",
        "DOGE-USD", "ADA-USD", "TRX-USD", "AVAX-USD", "SHIB-USD",
        "DOT-USD", "LINK-USD", "BCH-USD", "NEAR-USD", "LTC-USD",
        "ICP-USD", "UNI7083-USD", "ETC-USD", "XLM-USD", "ATOM-USD",
    )

    # Benchmark for every comparison.
    benchmark: str = "buy_and_hold"

    # Bar interval used for the dry run. Daily bars keep Phase 1 simple and
    # cheap; Phase 2 (forward paper trading) can move to intraday bars once
    # the pipeline is proven.
    bar_interval: str = "1d"

    # How many bars of history to fetch for the dry run.
    lookback_days: int = 400

    # Holding period for a single decision, in bars.
    holding_period_bars: int = 5

    # Fixed position-sizing rule (fraction of a notional portfolio per
    # decision). Mechanical, not optimized.
    position_size_fraction: float = 0.10

    # Portfolio-level cap on gross exposure (sum of size_fraction across all
    # positions approved in one run) that risk_check() enforces alongside
    # its per-position sizing. With only 2 tickers this could never bind
    # (2 * 0.10 = 0.20 << 1.0); added when the universe grew to 20, where an
    # uncapped run could otherwise approve up to 20 * 0.10 = 2.00 (200% of
    # notional) if every name signaled LONG the same day (e.g. a
    # market-wide rally) — same fixed 10%-per-name rule, just no longer
    # allowed to compound past 100% in aggregate.
    max_gross_exposure_fraction: float = 1.0

    # Cost assumptions applied when scoring outcomes. These matter a lot for
    # the stated falsification bar ("edge disappears after costs").
    taker_fee_bps: float = 10.0     # 0.10% per side, a plausible spot-market retail taker fee
    slippage_bps: float = 5.0       # 0.05% assumed slippage per side

    # Output locations.
    data_dir: str = "data"
    output_dir: str = "output"

    # The REAL-evidence journal: every row here comes from
    # run_paper_trading.py (Phase 2) and is a data_source="REAL:*" row --
    # see RESEARCH_SPEC.md. This is the only file Phase 2's evidence count
    # is ever read from.
    journal_path: str = "output/decision_journal.jsonl"

    # Phase 1's own, entirely separate journal (data_source="SYNTHETIC"
    # only). run_dry_run.py deletes and regenerates this file on every run
    # (Phase 1 is a repeatable, non-evidentiary smoke test, not a log to
    # preserve) -- it used to share journal_path with Phase 2, which meant
    # every Phase 1 re-run destroyed Phase 2's real evidence too. Split out
    # on 2026-09-14; see RESEARCH_SPEC.md's "Journal separation" note.
    phase1_journal_path: str = "output/phase1_dry_run_journal.jsonl"

    dry_run_summary_path: str = "output/phase1_dry_run_summary.csv"


CONFIG = Config()
