"""
The frozen six-step workflow, in fixed order:

  1. gather_data
  2. form_thesis
  3. risk_check
  4. decide
  5. log
  6. review (later, once the holding period has elapsed)

Steps 1-5 run together at "signal time" for a given bar. Step 6 runs later,
once enough bars have passed, and only touches records already in the
journal — it never re-runs steps 1-5.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Optional

import pandas as pd

from . import journal as journal_mod
from .risk import risk_check
from .thesis import Thesis, stub_form_thesis


ThesisFn = Callable[[str, pd.DataFrame], Thesis]

# Safety net for run_review_step, independent of any specific known bug: no
# legitimate 5-bar-holding-period crypto swing should ever produce a return
# outside this bound. It exists to fail loudly on the *next* scale-mismatch
# or bad-data-provider bug (entry/exit prices from two incompatible sources,
# a stock-split-style data glitch, etc.) instead of silently writing a
# nonsense outcome into the immutable journal -- which is exactly what
# happened once already: a SYNTHETIC (~$100-scale) entry price reviewed
# against a REAL (~$77,000-scale) exit price produced a 760x "return." 500%
# is already far beyond a plausible outcome for this project's universe and
# holding period, even for a volatile small-cap coin, while still nowhere
# near the ~760x/~38x magnitude that bug produced.
MAX_SANE_ABS_RETURN = 5.0  # 500%


def gather_data(full_history: pd.DataFrame, as_of_date: pd.Timestamp) -> pd.DataFrame:
    """
    Return only bars available as of `as_of_date` (inclusive). This is the
    no-lookahead guard: nothing downstream ever sees a bar dated after
    as_of_date.
    """
    return full_history.loc[full_history.index <= as_of_date]


def decide(risk_decision) -> str:
    return "BUY" if risk_decision.approved else "HOLD"


def run_signal_step(
    ticker: str,
    full_history: pd.DataFrame,
    as_of_date: pd.Timestamp,
    journal_path: str,
    position_size_fraction: float,
    data_source: str,
    thesis_fn: ThesisFn = stub_form_thesis,
    run_timestamp: Optional[str] = None,
    current_gross_exposure: float = 0.0,
    max_gross_exposure_fraction: float = 1.0,
    write_to_journal: bool = True,
) -> journal_mod.JournalRecord:
    """
    Execute steps 1-5 for a single ticker at a single decision date, and
    (by default) append the result to the journal. Returns the record.

    `current_gross_exposure` / `max_gross_exposure_fraction` pass straight
    through to risk_check() -- see its docstring. Both default to values
    that make the portfolio-level cap a no-op, so this stays backward
    compatible with every existing call site.

    `write_to_journal=False` skips step 5's disk write and just returns the
    record -- for a caller logging many records from one process invocation
    (Phase 1's dry run) that wants to batch them into one
    journal.append_decisions() call instead of one append_decision() call
    per record (each of which is a full read+rewrite+fsync -- see
    append_decisions()'s docstring for why that matters at volume). Step 5
    ("log") still logically happens for every record either way; this only
    changes whether THIS call performs its own disk write immediately, not
    whether the record ever gets logged.
    """
    # 1. gather_data — enforce no-lookahead
    visible = gather_data(full_history, as_of_date)
    if visible.empty or visible.index[-1] != as_of_date:
        raise ValueError(f"No bar for {ticker} on {as_of_date}; cannot signal.")

    # 2. form_thesis
    thesis = thesis_fn(ticker, visible)

    # 3. risk_check
    risk = risk_check(
        thesis,
        position_size_fraction,
        current_gross_exposure=current_gross_exposure,
        max_gross_exposure_fraction=max_gross_exposure_fraction,
    )

    # 4. decide
    action = decide(risk)

    # Entry is the NEXT bar's open, not this bar's close — consistent with
    # the original project's next-open convention to avoid same-bar
    # execution lookahead. In Phase 1 dry run we only know entry price if
    # the next bar exists in our synthetic/historical frame.
    #
    # entry_date/signal_date/exit_date are stored as the FULL timestamp
    # string (str(ts), not str(ts.date())) so this works correctly at any
    # bar_interval, not just "1d" -- at "1h", two different bars on the
    # same calendar date would collapse into the same signal_date/entry_date
    # under date-only truncation, breaking _already_signaled's (ticker,
    # date) uniqueness check and run_review_step's index lookup alike. For
    # "1d" bars (whose timestamps are always midnight) this just means the
    # stored string now reads "2026-09-15 00:00:00" instead of
    # "2026-09-15" -- same day, same meaning, no behavior change.
    idx = full_history.index.get_loc(as_of_date)
    entry_date = None
    entry_price = None
    if action == "BUY" and idx + 1 < len(full_history):
        entry_date = str(full_history.index[idx + 1])
        entry_price = float(full_history["Open"].iloc[idx + 1])

    record = journal_mod.JournalRecord(
        record_id=str(uuid.uuid4()),
        run_timestamp=run_timestamp or datetime.now(timezone.utc).isoformat(),
        ticker=ticker,
        signal_date=str(as_of_date),
        thesis_direction=thesis.direction,
        thesis_confidence=thesis.confidence,
        thesis_reasoning=thesis.reasoning,
        thesis_source=thesis.source,
        risk_approved=risk.approved,
        risk_size_fraction=risk.size_fraction,
        risk_reason=risk.reason,
        action=action,
        entry_date=entry_date,
        entry_price=entry_price,
        data_source=data_source,
    )

    # 5. log — append-only, refuses duplicates
    if write_to_journal:
        journal_mod.append_decision(journal_path, record)
    return record


def run_review_step(
    record: dict,
    full_history: pd.DataFrame,
    holding_period_bars: int,
    journal_path: str,
    taker_fee_bps: float,
    slippage_bps: float,
    benchmark_history: pd.DataFrame,
    write_to_journal: bool = True,
) -> Optional[dict]:
    """
    6. review — if the holding period has elapsed since entry, compute and
    (by default) append the realized outcome. Returns the updated record
    dict, or None if the review wasn't applicable/ready yet.

    `write_to_journal=False` skips the disk write and just returns the
    updated dict -- same batching rationale as run_signal_step's, for a
    caller (Phase 1's dry run) that wants to collect many outcomes and
    apply them in one journal.append_outcomes() call. See that function's
    docstring.
    """
    if record["action"] != "BUY" or record["outcome_status"] == "COMPLETE":
        return None
    if record["entry_date"] is None:
        return None

    entry_date = pd.Timestamp(record["entry_date"])
    if entry_date not in full_history.index:
        return None
    entry_idx = full_history.index.get_loc(entry_date)
    exit_idx = entry_idx + holding_period_bars
    if exit_idx >= len(full_history):
        return None  # not enough bars yet — stays PENDING

    exit_date = full_history.index[exit_idx]
    exit_price = float(full_history["Open"].iloc[exit_idx])
    entry_price = record["entry_price"]

    stock_return = exit_price / entry_price - 1

    if abs(stock_return) > MAX_SANE_ABS_RETURN:
        raise RuntimeError(
            f"run_review_step({record['ticker']}, {record['record_id']}): computed "
            f"stock_return={stock_return:.4%} exceeds the {MAX_SANE_ABS_RETURN:.0%} sanity "
            f"bound (entry_price={entry_price!r} on {record['entry_date']}, "
            f"exit_price={exit_price!r} on {exit_date}). Refusing to write this outcome "
            f"-- this smells like mismatched data sources (e.g. a SYNTHETIC entry reviewed "
            f"against a REAL exit) or a bad price from the data provider, not a real market move."
        )

    # Benchmark: buy-and-hold over the identical entry/exit dates.
    bench_entry = float(benchmark_history["Open"].loc[entry_date])
    bench_exit = float(benchmark_history["Open"].loc[exit_date])
    benchmark_return = bench_exit / bench_entry - 1

    excess_return = stock_return - benchmark_return

    # Cost model: fee + slippage applied on both entry and exit (round trip).
    round_trip_cost = 2 * (taker_fee_bps + slippage_bps) / 10_000
    net_of_cost_return = stock_return - round_trip_cost

    if write_to_journal:
        journal_mod.append_outcome(
            journal_path,
            record_id=record["record_id"],
            exit_date=str(exit_date),
            exit_price=exit_price,
            stock_return=stock_return,
            benchmark_return=benchmark_return,
            excess_return=excess_return,
            net_of_cost_return=net_of_cost_return,
        )

    record = dict(record)
    record.update(
        outcome_status="COMPLETE",
        exit_date=str(exit_date),
        exit_price=exit_price,
        stock_return=stock_return,
        benchmark_return=benchmark_return,
        excess_return=excess_return,
        net_of_cost_return=net_of_cost_return,
    )
    return record
