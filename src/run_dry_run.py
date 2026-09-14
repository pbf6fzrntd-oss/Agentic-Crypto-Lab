"""
Phase 1 — Mechanical Dry Run.

Runs the frozen six-step workflow over synthetic OHLCV data for the fixed
universe, end to end, and prints a summary.

REMINDER (see RESEARCH_SPEC.md): this run uses SYNTHETIC data and a STUB
(non-LLM) thesis step. Its output proves the pipeline works; it is NOT
evidence about the workflow's real trading quality. Do not report numbers
from this run as if they were a backtest result.

Run with:  python3 -m src.run_dry_run
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running as `python3 -m src.run_dry_run` from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from src.config import CONFIG
from src.data import generate_synthetic_ohlcv, validate_ohlcv
from src.journal import load_journal
from src.workflow import run_review_step, run_signal_step


def main() -> None:
    print("=" * 70)
    print("PHASE 1 — MECHANICAL DRY RUN (synthetic data, stub thesis)")
    print("This run is NOT evidence. It validates the pipeline only.")
    print("=" * 70)

    journal_path = CONFIG.journal_path
    Path(journal_path).parent.mkdir(parents=True, exist_ok=True)
    if Path(journal_path).exists():
        Path(journal_path).unlink()  # fresh journal each dry run

    # Use a fixed benchmark series too (synthetic "buy-and-hold" reference).
    benchmark_history = generate_synthetic_ohlcv(
        "SYNTH-BENCHMARK", n_bars=CONFIG.lookback_days, seed=999, start_price=100.0
    )

    histories = {}
    for i, ticker in enumerate(CONFIG.universe):
        hist = generate_synthetic_ohlcv(ticker, n_bars=CONFIG.lookback_days, seed=100 + i)
        problems = validate_ohlcv(hist, ticker)
        if problems:
            print(f"[DATA VALIDATION FAILED] {ticker}: {problems}")
            continue
        histories[ticker] = hist
        print(f"[OK] {ticker}: {len(hist)} synthetic daily bars validated, data_source=SYNTHETIC")

    if not histories:
        print("No valid data for any ticker. Aborting.")
        return

    # --- Signal generation over the whole window (steps 1-5) ---
    signal_count = 0
    for ticker, hist in histories.items():
        # Skip the first 5 bars (need lookback for the stub thesis) and the
        # last bar (need a next-bar open for entry).
        for as_of_date in hist.index[5:-1]:
            record = run_signal_step(
                ticker=ticker,
                full_history=hist,
                as_of_date=as_of_date,
                journal_path=journal_path,
                position_size_fraction=CONFIG.position_size_fraction,
                data_source="SYNTHETIC",
            )
            if record.action == "BUY":
                signal_count += 1

    print(f"\nSignal generation complete. {signal_count} BUY decisions logged.")

    # --- Review pass (step 6) ---
    rows = load_journal(journal_path)
    completed = 0
    for row in rows:
        hist = histories[row["ticker"]]
        updated = run_review_step(
            record=row,
            full_history=hist,
            holding_period_bars=CONFIG.holding_period_bars,
            journal_path=journal_path,
            taker_fee_bps=CONFIG.taker_fee_bps,
            slippage_bps=CONFIG.slippage_bps,
            benchmark_history=benchmark_history,
        )
        if updated is not None:
            completed += 1

    print(f"Review pass complete. {completed} outcomes completed.")

    # --- Summary (non-evidentiary, plumbing check only) ---
    rows = load_journal(journal_path)
    df = pd.DataFrame(rows)
    complete = df[df["outcome_status"] == "COMPLETE"]

    print("\n" + "=" * 70)
    print("PIPELINE SMOKE-TEST SUMMARY (synthetic data — not evidence)")
    print("=" * 70)
    print(f"Total decisions logged: {len(df)}")
    print(f"BUY decisions: {(df['action'] == 'BUY').sum()}")
    print(f"HOLD decisions: {(df['action'] == 'HOLD').sum()}")
    print(f"Completed outcomes: {len(complete)}  |  Pending: {(df['outcome_status'] == 'PENDING').sum()}")
    if len(complete):
        print(f"Mean raw excess return (synthetic, gross): {complete['excess_return'].mean():.4%}")
        print(f"Mean net-of-cost return (synthetic): {complete['net_of_cost_return'].mean():.4%}")
    print("\nReminder: these numbers come from a random-walk synthetic series")
    print("and a non-LLM stub thesis. They demonstrate the pipeline runs")
    print("correctly end-to-end. They say nothing about real trading quality.")

    df.to_csv(CONFIG.dry_run_summary_path, index=False)
    print(f"\nFull journal written to: {journal_path}")
    print(f"Summary CSV written to: {CONFIG.dry_run_summary_path}")


if __name__ == "__main__":
    main()
