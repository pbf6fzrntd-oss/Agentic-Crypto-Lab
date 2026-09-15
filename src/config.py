"""
Frozen parameters for Phase 1 (mechanical dry run).

Do not tune these against results. See RESEARCH_SPEC.md for the rules this
project is bound by.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Config:
    # Fixed universe — the top 20 non-stablecoin cryptocurrencies by REAL
    # market cap, chosen (like the original BTC/ETH pair) for data
    # availability and liquidity, not for any expected edge. Expanded from
    # (BTC-USD, ETH-USD) on 2026-09-14, corrected against live market-cap
    # data on 2026-09-15 (see RESEARCH_SPEC.md's "Universe expansion" and
    # "Universe correction" notes) — both changes made BEFORE any Phase 2
    # outcome had completed.
    #
    # UNI7083-USD/TON11419-USD/SUI20947-USD are Yahoo Finance's
    # disambiguated symbols for Uniswap/Toncoin/Sui (the plain "UNI-USD"/
    # "SUI-USD" tickers return no data, and plain "TON-USD" resolves to an
    # unrelated project called "TON Token" -- caught the same way the
    # "ARB-USD" -> "ARbit" collision was caught below). Every symbol here
    # was confirmed via this project's own fetch_ohlcv() to return real,
    # validate_ohlcv()-clean data AT THE CURRENT bar_interval ("1h") before
    # being added, and identity-checked (longName) to rule out a
    # same-symbol collision with an unrelated asset -- that check also
    # excluded plain "ARB-USD" (resolves to "ARbit", not Arbitrum; neither
    # spelling of Arbitrum made the real top 20 either way).
    #
    # Two pegged/derivative tokens were deliberately excluded despite
    # ranking within the raw top 20 by market cap: Lido Staked ETH
    # (STETH-USD, tracks ETH 1:1 plus staking yield) and Wrapped Bitcoin
    # (WBTC-USD, tracks BTC 1:1) — same rationale RESEARCH_SPEC.md already
    # applies to stablecoins ("a pegged asset has no meaningful directional
    # thesis... would dilute not test the hypothesis"): both are
    # near-perfectly correlated with an asset already in this universe
    # (ETH, BTC), so including them wouldn't add independent exposure, just
    # double up on BTC/ETH under a different ticker.
    universe: tuple = (
        "BTC-USD", "ETH-USD", "BNB-USD", "XRP-USD", "SOL-USD",
        "TRX-USD", "DOGE-USD", "XMR-USD", "LINK-USD", "ADA-USD",
        "XLM-USD", "TON11419-USD", "BCH-USD", "UNI7083-USD", "LTC-USD",
        "HBAR-USD", "AVAX-USD", "NEAR-USD", "SHIB-USD", "SUI20947-USD",
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

    # src/run_historical_validation.py's own journal -- REAL 12-month daily
    # price history (Yahoo Finance) but the NON-LLM stub_form_thesis, same
    # as Phase 1. Entirely separate from journal_path (Phase 2's real
    # evidence) and phase1_journal_path (Phase 1's synthetic data): this is
    # a THIRD, equally non-evidentiary category -- real prices, fake
    # thesis -- and must never be mistaken for either. See
    # RESEARCH_SPEC.md's "Historical validation" note for why it can't
    # speed up the falsification check no matter how much real price
    # history it runs against.
    historical_journal_path: str = "output/historical_validation_journal.jsonl"
    historical_summary_path: str = "output/historical_validation_summary.csv"

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
