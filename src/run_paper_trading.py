"""
Phase 2 — Forward Paper Trading runner.

Runs the SAME frozen six-step workflow as Phase 1 (gather_data -> form_thesis
-> risk_check -> decide -> log -> review; see workflow.py), but on REAL data
via fetch_ohlcv() and a REAL Claude call via form_thesis_llm() instead of
synthetic data and a stub. This is the actual evidence-gathering phase of
the project — see RESEARCH_SPEC.md. Phase 1's numbers were never evidence;
every row this script appends starts the real evidence count at zero.

HARD CONSTRAINT — READ THIS BEFORE MODIFYING THIS FILE:
This module NEVER places a real order on any exchange, anywhere, under any
condition. It only ever reads public OHLCV market data (via
src.data.fetch_ohlcv) and computes HYPOTHETICAL entry/exit prices and
returns from it. There is no exchange authentication, no order-placement
call, no private/trading API of any kind in this file or in anything it
imports. If you are adding a feature here, it must stay that way — no
exchange client is ever constructed with API keys/secrets for trading, and
no "place_order" / "create_order" / execution call is ever added. Grep this
file (and src/data.py) for "order" if you need to re-verify that.

WHAT THIS SCRIPT DOES, ONCE, PER INVOCATION (it does not loop internally —
invoke it periodically via cron / a scheduled task / by hand):
  1. Fetches the latest real bars for each ticker in CONFIG.universe.
  2. For each ticker, checks the most recent decision-eligible bar (the
     second-to-last fetched bar — see _select_signal_date below for why)
     and, if a decision for that (ticker, date) isn't already in the
     journal, runs steps 1-5 of the workflow with REAL data and a REAL LLM
     thesis call, and appends the result.
  3. Reviews every still-PENDING journal row whose holding period has now
     elapsed, using real exit prices, and appends the realized outcome.
  4. Prints a concise summary: new decisions logged, outcomes completed,
     and the current pending count.

Run with:  python3 -m src.run_paper_trading

COST: each run makes one real Claude API call per ticker that gets a new
signal (not one per review). See the researcher-facing cost estimate in the
project's Phase 2 write-up / commit message before scheduling this.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from src.config import CONFIG
from src.data import fetch_ohlcv, validate_ohlcv
from src.journal import load_journal
from src.thesis import form_thesis_llm
from src.workflow import run_review_step, run_signal_step


def _already_signaled(rows: list[dict], ticker: str, signal_date: str) -> bool:
    """
    Idempotency guard: if this script is invoked more than once on the same
    period (e.g. re-run by accident), never log a second decision — and
    never make a second billed LLM call — for a (ticker, signal_date) pair
    already in the journal.
    """
    return any(r["ticker"] == ticker and r["signal_date"] == signal_date for r in rows)


def _is_reviewable_with_real_data(row: dict) -> bool:
    """
    Guard for the review pass: a journal row may only be reviewed against
    the real price history fetched this run if IT was itself decided from
    real data. A Phase 1 row (`data_source == "SYNTHETIC"`) uses an
    unrelated price scale (synthetic bars start around $100; real BTC/ETH
    bars don't) — matching its entry_date string against real history would
    "complete" it with a fabricated outcome (e.g. a bogus 700x return)
    instead of correctly leaving it PENDING forever. Phase 1 rows are never
    evidence and must never be touched by this runner.
    """
    return str(row.get("data_source", "")).startswith("REAL")


def _select_signal_date(hist: pd.DataFrame) -> pd.Timestamp:
    """
    Pick the one bar to signal on this run: the SECOND-TO-LAST fetched bar.

    Entry price is the next bar's open (workflow.run_signal_step's fixed
    convention, same as Phase 1). In a forward run the very last fetched
    bar's "next bar" hasn't happened yet, so signaling on it would leave
    entry_price permanently unknowable. Signaling on the second-to-last bar
    means its "next bar" (the last fetched bar) has already closed, so a
    real entry price is already known — this mirrors exactly what Phase 1's
    dry-run loop did (`hist.index[5:-1]`, excluding the final bar), just one
    date per run instead of backfilling the whole history at once.
    """
    return hist.index[-2]


def _build_benchmark(histories: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Real-data buy-and-hold benchmark for run_review_step's excess_return
    calculation: an equal-weighted basket of the fixed universe, each leg
    normalized to 100 at the start of its own fetched history and averaged.

    NOTE ON WHY THIS ISN'T "the same instrument" literally: RESEARCH_SPEC.md
    says the benchmark is buy-and-hold on the same instrument over the same
    window. But run_review_step looks up the benchmark's price on the
    trade's own entry_date/exit_date — if benchmark_history were literally
    the traded ticker's own price series, benchmark_return would equal
    stock_return exactly on every single trade (same dates, same prices),
    making excess_return trivially zero always. That can't be the intended
    comparison, and fixing it would mean changing run_review_step's frozen
    math, which is out of scope here. This basket is the closest
    non-degenerate, still-real-data, still-buy-and-hold stand-in; flagged
    explicitly to the researcher rather than decided silently — see
    RESEARCH_SPEC.md's Phase 2 note and the PR description.
    """
    normalized = []
    for hist in histories.values():
        base = hist["Open"].iloc[0]
        normalized.append(hist["Open"] / base * 100.0)
    combined = pd.concat(normalized, axis=1).mean(axis=1).dropna()
    bench = pd.DataFrame({"Open": combined})
    bench.index.name = "Date"
    return bench


def main() -> None:
    print("=" * 70)
    print("PHASE 2 — FORWARD PAPER TRADING (real data, live LLM thesis)")
    print("PAPER TRADING ONLY. No real order is ever placed by this script.")
    print("=" * 70)

    journal_path = CONFIG.journal_path
    Path(journal_path).parent.mkdir(parents=True, exist_ok=True)

    histories: dict[str, pd.DataFrame] = {}
    for ticker in CONFIG.universe:
        try:
            hist = fetch_ohlcv(ticker, lookback_days=CONFIG.lookback_days, interval=CONFIG.bar_interval)
        except Exception as exc:  # noqa: BLE001 — never fabricate data on a fetch failure
            print(f"[FETCH FAILED] {ticker}: {exc}")
            continue

        problems = validate_ohlcv(hist, ticker)
        if problems:
            print(f"[DATA VALIDATION FAILED] {ticker}: {problems}")
            print(f"  Skipping {ticker} this run — not logging any decision on unvalidated data.")
            continue

        histories[ticker] = hist
        print(
            f"[OK] {ticker}: {len(hist)} real daily bars validated "
            f"(source={hist.attrs.get('data_source', 'REAL')})"
        )

    if not histories:
        print("No valid real data for any ticker this run. Aborting.")
        return

    benchmark_history = _build_benchmark(histories)
    existing_rows = load_journal(journal_path)

    # --- Signal pass (steps 1-5), one decision-eligible date per ticker ---
    new_decisions = 0
    errored_tickers = []
    for ticker, hist in histories.items():
        if len(hist) < 6:
            print(f"[SKIP] {ticker}: not enough history yet for a signal ({len(hist)} bars).")
            continue

        as_of_date = _select_signal_date(hist)
        signal_date = str(as_of_date.date())

        if _already_signaled(existing_rows, ticker, signal_date):
            print(f"[SKIP] {ticker}: already have a decision logged for {signal_date}.")
            continue

        try:
            record = run_signal_step(
                ticker=ticker,
                full_history=hist,
                as_of_date=as_of_date,
                journal_path=journal_path,
                position_size_fraction=CONFIG.position_size_fraction,
                data_source=hist.attrs.get("data_source", "REAL"),
                thesis_fn=form_thesis_llm,
            )
        except Exception as exc:  # noqa: BLE001 — never fabricate a decision on LLM/log failure
            print(f"[ERROR] {ticker}: thesis/log step failed, skipping this run: {exc}")
            errored_tickers.append(ticker)
            continue

        new_decisions += 1
        print(
            f"  {ticker} {signal_date}: {record.action} "
            f"(direction={record.thesis_direction}, confidence={record.thesis_confidence:.2f})"
        )

    # --- Review pass (step 6): complete any PENDING BUY whose holding
    # period has now elapsed, using real prices. Never touches decision-time
    # fields — see journal.append_outcome. ---
    rows = load_journal(journal_path)
    completed_this_run = 0
    for row in rows:
        ticker = row["ticker"]
        if ticker not in histories:
            continue  # can't review without this ticker's real data this run
        if not _is_reviewable_with_real_data(row):
            continue
        updated = run_review_step(
            record=row,
            full_history=histories[ticker],
            holding_period_bars=CONFIG.holding_period_bars,
            journal_path=journal_path,
            taker_fee_bps=CONFIG.taker_fee_bps,
            slippage_bps=CONFIG.slippage_bps,
            benchmark_history=benchmark_history,
        )
        if updated is not None:
            completed_this_run += 1
            print(
                f"  Outcome completed: {ticker} {row['signal_date']} -> "
                f"net_of_cost_return={updated['net_of_cost_return']:.4%}"
            )

    rows = load_journal(journal_path)
    pending = sum(1 for r in rows if r["outcome_status"] == "PENDING")

    print("\n" + "=" * 70)
    print("RUN SUMMARY")
    print("=" * 70)
    print(f"New decisions logged this run: {new_decisions}")
    print(f"Outcomes completed this run: {completed_this_run}")
    print(f"Currently pending: {pending}")
    print(f"Total journal rows: {len(rows)}")
    if errored_tickers:
        print(f"Tickers skipped due to errors this run: {errored_tickers}")
    print(
        "\nReminder: Phase 2 evidence accumulates only from completed real "
        "outcomes above. Zero completed outcomes on an early run is "
        "expected, not a problem."
    )


if __name__ == "__main__":
    main()
