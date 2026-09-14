"""
Frozen parameters for Phase 1 (mechanical dry run).

Do not tune these against results. See RESEARCH_SPEC.md for the rules this
project is bound by.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Config:
    # Fixed universe — small and liquid, chosen for data availability, not
    # for any expected edge.
    universe: tuple = ("BTC-USD", "ETH-USD")

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

    # Cost assumptions applied when scoring outcomes. These matter a lot for
    # the stated falsification bar ("edge disappears after costs").
    taker_fee_bps: float = 10.0     # 0.10% per side, a plausible spot-market retail taker fee
    slippage_bps: float = 5.0       # 0.05% assumed slippage per side

    # Output locations.
    data_dir: str = "data"
    output_dir: str = "output"
    journal_path: str = "output/decision_journal.jsonl"
    dry_run_summary_path: str = "output/phase1_dry_run_summary.csv"


CONFIG = Config()
