"""
Historical Validation ("Phase 1.5") -- mechanical pipeline check against
REAL price history. NOT EVIDENCE, and does not speed up Phase 2's
falsification check -- see the long note below before reading anything
into its output.

WHAT THIS IS: the same frozen six-step workflow as Phase 1, but fed REAL
daily OHLCV history (via fetch_ohlcv() / Yahoo Finance, the same function
Phase 2 uses) over the last HISTORICAL_LOOKBACK_DAYS instead of Phase 1's
synthetic random walk. Still uses stub_form_thesis() -- the same
deterministic, non-LLM momentum heuristic Phase 1 uses, NOT
form_thesis_llm().

HARD CONSTRAINT -- READ THIS BEFORE MODIFYING THIS FILE:
This module NEVER calls the Anthropic API and NEVER reads
ANTHROPIC_KEY_FOR_TRADING. It must not import or call form_thesis_llm, or
anything from src/cost_tracking.py. The whole point of this script is a
real-price mechanical check that costs nothing and can never contaminate
Phase 2's evidence -- if you're adding a feature here, it must stay that
way. Grep this file for "anthropic" or "form_thesis_llm" to re-verify.

WHY THIS IS **NOT EVIDENCE** AND DOES **NOT** SPEED UP THE FALSIFICATION
CHECK, NO MATTER HOW MUCH REAL PRICE HISTORY IT RUNS AGAINST:
RESEARCH_SPEC.md restricts real evidence to live, forward-only Phase 2
for one specific reason: a historical backtest of the LLM thesis step
can't be trusted, because the model may carry training-data knowledge of
what actually happened on any historical date it's shown -- a form of
lookahead bias no amount of careful timestamp handling fixes. This script
sidesteps that problem BY DEFINITION, by never asking the LLM anything --
but that means it can only ever test the MECHANICAL parts of the pipeline
(does real data validate cleanly, does the cost model behave sensibly,
does no-lookahead hold, what would a purely mechanical non-LLM rule have
done) against real market history. It cannot tell you anything about
whether the LLM's actual judgment has edge, which is the entire research
question Phase 2 exists to answer. Its numbers are exactly as
non-evidentiary as Phase 1's synthetic-data numbers -- just real prices
under a fake thesis, instead of fake prices under a fake thesis.

SCOPE NOTE: unlike run_paper_trading.py, this does NOT apply the
portfolio-level gross-exposure cap (risk.py's max_gross_exposure_fraction)
-- it mirrors Phase 1's simpler per-ticker-independent backfill exactly
(see run_dry_run.py), which never tracked cross-ticker exposure either.
Adding cap-aware, date-synchronized backfilling across 20 tickers was out
of scope for a script whose numbers are non-evidentiary either way.

Run with: python3 -m src.run_historical_validation
Writes: Config.historical_journal_path, Config.historical_summary_path
"""

from __future__ import annotations

import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from src.config import CONFIG
from src.data import fetch_ohlcv, validate_ohlcv
from src.journal import append_decisions, append_outcomes, load_journal
from src.run_paper_trading import _build_benchmark
from src.thesis import stub_form_thesis
from src.workflow import run_review_step, run_signal_step

# How much REAL daily history to pull per ticker. A module constant, not a
# CONFIG field -- like thesis.py's CONTEXT_BARS, this is specific to this
# one analysis script's scope, not a frozen research parameter shared
# across phases.
HISTORICAL_LOOKBACK_DAYS = 365

# 5 daily bars = 5 real days, matching the original (pre-hourly-cadence)
# holding period and the "~5 trading days" framing still hardcoded into
# thesis.py's LLM system prompt -- kept consistent even though this script
# never calls that prompt, so its baseline is comparable in kind to what
# the daily-cadence design originally measured.
HISTORICAL_HOLDING_PERIOD_BARS = 5


def main() -> None:
    print("=" * 70)
    print("HISTORICAL VALIDATION (\"Phase 1.5\") -- REAL prices, STUB thesis")
    print("NOT EVIDENCE. Does not use the Anthropic API. Does not speed up")
    print("the falsification check -- see this file's module docstring.")
    print("=" * 70)

    journal_path = CONFIG.historical_journal_path
    Path(journal_path).parent.mkdir(parents=True, exist_ok=True)
    if Path(journal_path).exists():
        Path(journal_path).unlink()  # fresh journal each run, like Phase 1

    histories: dict[str, pd.DataFrame] = {}
    for ticker in CONFIG.universe:
        try:
            hist = fetch_ohlcv(ticker, lookback_days=HISTORICAL_LOOKBACK_DAYS, interval="1d")
        except Exception as exc:  # noqa: BLE001 — never fabricate data on a fetch failure
            print(f"[FETCH FAILED] {ticker}: {exc}")
            continue

        problems = validate_ohlcv(hist, ticker)
        if problems:
            print(f"[DATA VALIDATION FAILED] {ticker}: {problems}")
            print(f"  Skipping {ticker} -- not backfilling on unvalidated real data.")
            continue

        histories[ticker] = hist
        print(f"[OK] {ticker}: {len(hist)} real daily bars validated (source={hist.attrs.get('data_source')})")

    if not histories:
        print("No valid real data for any ticker. Aborting.")
        return

    benchmark_history = _build_benchmark(histories)

    # --- Signal generation over the whole window (steps 1-5), batched --
    # same rationale as run_dry_run.py: thousands of records in one
    # invocation, so write_to_journal=False + one append_decisions() call
    # instead of one disk write per record. See journal.append_decisions().
    signal_records = []
    signal_count = 0
    for ticker, hist in histories.items():
        for as_of_date in hist.index[5:-1]:
            record = run_signal_step(
                ticker=ticker,
                full_history=hist,
                as_of_date=as_of_date,
                journal_path=journal_path,
                position_size_fraction=CONFIG.position_size_fraction,
                data_source=hist.attrs.get("data_source", "REAL"),
                thesis_fn=stub_form_thesis,
                write_to_journal=False,
            )
            signal_records.append(record)
            if record.action == "BUY":
                signal_count += 1

    append_decisions(journal_path, signal_records)
    print(f"\nSignal generation complete. {signal_count} BUY decisions logged (of {len(signal_records)} total).")

    # --- Review pass (step 6), also batched ---
    rows = [asdict(r) for r in signal_records]
    outcomes = []
    for row in rows:
        hist = histories[row["ticker"]]
        updated = run_review_step(
            record=row,
            full_history=hist,
            holding_period_bars=HISTORICAL_HOLDING_PERIOD_BARS,
            journal_path=journal_path,
            taker_fee_bps=CONFIG.taker_fee_bps,
            slippage_bps=CONFIG.slippage_bps,
            benchmark_history=benchmark_history,
            write_to_journal=False,
        )
        if updated is not None:
            outcomes.append(updated)

    append_outcomes(journal_path, outcomes)
    print(f"Review pass complete. {len(outcomes)} outcomes completed.")

    # --- Summary ---
    all_rows = load_journal(journal_path)
    df = pd.DataFrame(all_rows)
    complete = df[df["outcome_status"] == "COMPLETE"]

    print("\n" + "=" * 70)
    print("HISTORICAL VALIDATION SUMMARY (real prices, stub thesis -- NOT EVIDENCE)")
    print("=" * 70)
    print(f"Tickers included: {len(histories)} of {len(CONFIG.universe)} (see [DATA VALIDATION FAILED]/[FETCH FAILED] above for any skipped)")
    print(f"Total decisions: {len(df)}")
    print(f"BUY decisions: {(df['action'] == 'BUY').sum()}")
    print(f"HOLD decisions: {(df['action'] == 'HOLD').sum()}")
    print(f"Completed outcomes: {len(complete)}  |  Pending (ran out of window): {(df['outcome_status'] == 'PENDING').sum()}")
    if len(complete):
        print(f"Mean raw excess return (mechanical stub, real prices): {complete['excess_return'].mean():.4%}")
        print(f"Mean net-of-cost return (mechanical stub, real prices): {complete['net_of_cost_return'].mean():.4%}")
    print(
        "\nReminder: this is a NON-LLM stub thesis run against REAL prices. It "
        "validates the mechanical pipeline and shows what a purely mechanical "
        "momentum rule would have done -- it says NOTHING about the LLM "
        "thesis step's real quality, and is not a substitute for Phase 2's "
        "real-time evidence. See RESEARCH_SPEC.md's \"Historical validation\" note."
    )

    df.to_csv(CONFIG.historical_summary_path, index=False)
    print(f"\nFull journal written to: {journal_path}")
    print(f"Summary CSV written to: {CONFIG.historical_summary_path}")


if __name__ == "__main__":
    main()
