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

    # Bar interval Phase 2 trades on. Switched from "1d" to "1h" on
    # 2026-09-15 (with 19 real decisions logged and still ZERO completed
    # outcomes -- before any result existed to have tuned against; see
    # RESEARCH_SPEC.md's "Hourly cadence" note) to let the workflow signal
    # once per ticker per HOUR instead of once per day. NOTE: Phase 1's
    # generate_synthetic_ohlcv() does not implement bar_interval -- it
    # always simulates daily bars regardless of this setting. That's a
    # known, deliberately-deferred gap: Phase 1 is a non-evidentiary
    # plumbing smoke test, so it no longer interval-matches Phase 2, but
    # nothing about its validity as a smoke test depends on that match.
    bar_interval: str = "1h"

    # How many bars of history Phase 1's dry run generates (n_bars passed
    # straight to generate_synthetic_ohlcv, which is always daily -- see
    # bar_interval's note above). Phase 2's real fetch uses its own
    # phase2_lookback_days below instead, since the two now mean different
    # things at different scales.
    lookback_days: int = 400

    # Calendar days of real history fetch_ohlcv() pulls per ticker per
    # Phase 2 run (always calendar days, regardless of bar_interval -- see
    # fetch_ohlcv()'s docstring). 60 days at "1h" is ~1440 bars per ticker,
    # safely within yfinance's proven real depth for hourly crypto data
    # (tested live: ~99 days available) with comfortable headroom above
    # what CONTEXT_BARS + holding_period_bars actually need (60 + 120).
    phase2_lookback_days: int = 60

    # Holding period for a single decision, in bars. 120 hourly bars = 5
    # real days -- kept at the SAME real-world hold length as the original
    # daily-bar design (was 5 bars = 5 days) when bar_interval moved to
    # "1h", so this remains the same hypothesis (a ~5-trading-day view,
    # exactly what the LLM system prompt in thesis.py still says) decided
    # on more frequently, not a shorter hold layered on top of a frequency
    # change -- two research-parameter changes in one step would muddy
    # which one any observed effect came from.
    holding_period_bars: int = 120

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

    # Cost telemetry / circuit breaker for form_thesis_llm()'s real
    # Anthropic calls -- see src/cost_tracking.py. Every call is logged
    # here (append-only), and a new call is refused once today's estimated
    # spend reaches max_daily_cost_usd. Raised from $5.00 to $15.00 when
    # bar_interval moved to "1h": hourly signaling across the 20-ticker
    # universe runs ~20x more calls/day (~480 vs ~20), estimated at
    # ~$3.84/day in practice -- $15 keeps real headroom above that instead
    # of sitting within ~$1 of tripping on a slightly-above-average day.
    # Still a safety ceiling, not a tuned budget.
    cost_log_path: str = "output/llm_cost_log.jsonl"
    max_daily_cost_usd: float = 15.00

    # generate_report.py's output -- a human-readable summary of what the
    # REAL journal (journal_path) actually shows so far. Regenerated fresh
    # on every run (like dry_run_summary_path); never itself read back by
    # any other part of the pipeline.
    report_path: str = "output/phase2_daily_report.md"


CONFIG = Config()
