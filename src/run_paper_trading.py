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

Run with:  python3 -m src.run_paper_trading — invoke on a schedule matching
CONFIG.bar_interval (daily cron for "1d", the current default -- see
RESEARCH_SPEC.md's "Reverted to daily cadence" note for why hourly was
tried and reverted) for signals to actually materialize each period;
invoking more often than that is a harmless no-op (idempotency below
skips it), less often just means missed periods.

Note: main() fetches every (ticker, interval) pair actually needed this
run, not just CONFIG.universe x CONFIG.bar_interval -- an already-open
position from a ticker that's left the universe, or from BEFORE
bar_interval last changed, still needs its own (ticker, interval) fetched
so the review pass can complete it. See _entry_interval()'s docstring.

COST: each run makes one real Claude API call per ticker that gets a new
signal (not one per review) -- ~$0.0087/call measured live, enforced
against a hard daily cap by thesis.py/cost_tracking.py regardless. See
README.md's "Known limitations" -> Cost for the current per-run/per-day
estimate.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from src.config import CONFIG
from src.data import _BARS_PER_DAY, fetch_ohlcv, validate_ohlcv
from src.journal import load_journal
from src.thesis import form_thesis_llm
from src.workflow import run_review_step, run_signal_step


def _holding_period_bars_for(interval: str) -> int:
    """
    CONFIG.holding_period_bars is only correct FOR CONFIG.bar_interval --
    it's a bar count, not a calendar-time invariant, and different
    intervals pack different real-world time into one bar (120 hourly
    bars and 5 daily bars are both "5 real days", just expressed
    differently). Needed when reviewing a position opened under a
    since-changed interval (see _entry_interval): derive the equivalent
    bar count at that OTHER interval by converting through the real-world
    day count both express.
    """
    real_days = CONFIG.holding_period_bars / _BARS_PER_DAY[CONFIG.bar_interval]
    return round(real_days * _BARS_PER_DAY[interval])


def _already_signaled(rows: list[dict], ticker: str, signal_date: str) -> bool:
    """
    Idempotency guard: if this script is invoked more than once on the same
    period (e.g. re-run by accident), never log a second decision — and
    never make a second billed LLM call — for a (ticker, signal_date) pair
    already in the journal.

    Compares PARSED timestamps, not raw strings. signal_date has been
    stored in more than one string format across this project's history —
    see workflow.py's entry_date/signal_date note: a bare date
    ("2026-09-13", from before that fix) and a full timestamp
    ("2026-09-13 00:00:00", after it) name the exact same bar but are not
    equal as strings. Comparing raw strings let this guard miss the
    collision: 14 tickers got double-signaled (and double-billed) for the
    same real calendar day on 2026-09-13 before this was caught — see
    RESEARCH_SPEC.md's "Duplicate-signal guard hardened" note. Parsing
    both sides through pd.Timestamp before comparing closes this
    permanently, independent of which format either side happens to be in
    (old journal rows included — this is a read-time fix, the journal
    itself is never rewritten).
    """
    target = pd.Timestamp(signal_date)
    return any(
        r["ticker"] == ticker and pd.Timestamp(r["signal_date"]) == target
        for r in rows
    )


def _entry_interval(entry_date_str: str) -> str:
    """
    Infer which bar_interval a position was entered under, from its
    entry_date timestamp alone. A daily-bar entry always lands on midnight
    (yfinance's daily index is normalized to 00:00:00); an hourly-bar
    entry lands on whatever real hour it filled. Not stored explicitly on
    JournalRecord (no schema change needed) -- this heuristic is exact for
    every interval this project has ever used ("1d", "1h"), and exists so
    that if Config.bar_interval ever changes again (as it just did, twice,
    in one day), the review pass can still fetch the RIGHT granularity for
    each already-open position instead of silently never resolving it. See
    RESEARCH_SPEC.md's "Reverted to daily cadence" note for the concrete
    case that motivated this: 6 of 10 open positions were entered at "1h"
    precision when bar_interval reverted to "1d".
    """
    ts = pd.Timestamp(entry_date_str)
    return "1d" if (ts.hour, ts.minute, ts.second) == (0, 0, 0) else "1h"


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
    # sort=False: legs are already-aligned real price series, not needing
    # (and pandas 4.x now warning about implicitly getting) index sorting.
    combined = pd.concat(normalized, axis=1, sort=False).mean(axis=1).dropna()
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
    existing_rows = load_journal(journal_path)

    # Two independent reasons a (ticker, interval) pair outside
    # CONFIG.universe x CONFIG.bar_interval might still need fetching this
    # run, both because an already-open position must never be silently
    # orphaned:
    #   1. Ticker left the universe (e.g. the 2026-09-15 market-cap
    #      correction dropped DOT/ICP/ETC/ATOM) while still holding an
    #      open position.
    #   2. bar_interval changed (e.g. the 2026-09-15 "1h" -> back to "1d"
    #      reversion) while a position was open at the OLD interval -- its
    #      entry_date won't exist in newly-fetched data at the new
    #      interval, so review would silently never find it either.
    # Fetching CONFIG.universe x CONFIG.bar_interval alone would miss
    # both. Fetch every (ticker, interval) actually needed instead: each
    # universe ticker at the current interval (eligible for NEW signals),
    # plus each open position's own (ticker, its ENTRY interval) --
    # wind-down only, reviewed to completion, never signaled again.
    open_positions = [
        r for r in existing_rows
        if r["action"] == "BUY"
        and r["outcome_status"] == "PENDING"
        and r.get("data_source", "").startswith("REAL")
    ]
    needed: dict[tuple[str, str], bool] = {(t, CONFIG.bar_interval): False for t in CONFIG.universe}  # False = eligible for new signals
    for r in open_positions:
        key = (r["ticker"], _entry_interval(r["entry_date"]))
        needed.setdefault(key, True)  # True = wind-down only, never overrides a universe slot

    histories: dict[tuple[str, str], pd.DataFrame] = {}
    for (ticker, interval), wind_down_only in needed.items():
        try:
            hist = fetch_ohlcv(ticker, lookback_days=CONFIG.phase2_lookback_days, interval=interval)
        except Exception as exc:  # noqa: BLE001 — never fabricate data on a fetch failure
            print(f"[FETCH FAILED] {ticker} ({interval}): {exc}")
            continue

        problems = validate_ohlcv(hist, ticker)
        if problems:
            print(f"[DATA VALIDATION FAILED] {ticker} ({interval}): {problems}")
            print(f"  Skipping {ticker} ({interval}) this run — not acting on unvalidated data.")
            continue

        histories[(ticker, interval)] = hist
        note = " [wind-down only]" if wind_down_only else ""
        print(
            f"[OK] {ticker}: {len(hist)} real {interval} bars validated "
            f"(source={hist.attrs.get('data_source', 'REAL')}){note}"
        )

    if not histories:
        print("No valid real data for any ticker this run. Aborting.")
        return

    # One benchmark per interval actually in use this run -- a record's
    # review must compare against a benchmark built from the SAME
    # granularity its own entry/exit dates live in.
    intervals_used = {interval for (_, interval) in histories}
    benchmarks: dict[str, pd.DataFrame] = {
        interval: _build_benchmark({t: h for (t, i), h in histories.items() if i == interval})
        for interval in intervals_used
    }

    # --- Signal pass (steps 1-5), one decision-eligible date per ticker ---
    new_decisions = 0
    errored_tickers = []
    # Portfolio-level gross exposure -- accumulated here and passed into
    # risk_check() (via run_signal_step) so total exposure never exceeds
    # CONFIG.max_gross_exposure_fraction. MUST start from every still-open
    # (PENDING, REAL) position already in the journal, not just this run's
    # new approvals: with a 5-bar hold, up to 5 positions per ticker could
    # already be open and this cap would still never see them if it only
    # tracked same-run additions.
    gross_exposure = sum(r["risk_size_fraction"] for r in open_positions)
    for ticker in CONFIG.universe:
        # Only CONFIG.universe gets NEW signals -- a wind-down-only
        # (ticker, interval) pair is in `histories` purely so the review
        # pass below can still complete it, never to open a fresh position
        # (a ticker/interval no longer current must only wind down, never
        # gain MORE exposure).
        hist = histories.get((ticker, CONFIG.bar_interval))
        if hist is None:
            continue
        if len(hist) < 6:
            print(f"[SKIP] {ticker}: not enough history yet for a signal ({len(hist)} bars).")
            continue

        as_of_date = _select_signal_date(hist)
        signal_date = str(as_of_date)

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
                current_gross_exposure=gross_exposure,
                max_gross_exposure_fraction=CONFIG.max_gross_exposure_fraction,
            )
        except Exception as exc:  # noqa: BLE001 — never fabricate a decision on LLM/log failure
            print(f"[ERROR] {ticker}: thesis/log step failed, skipping this run: {exc}")
            errored_tickers.append(ticker)
            continue

        new_decisions += 1
        if record.risk_approved:
            gross_exposure += record.risk_size_fraction
        print(
            f"  {ticker} {signal_date}: {record.action} "
            f"(direction={record.thesis_direction}, confidence={record.thesis_confidence:.2f})"
            + (f" [{record.risk_reason}]" if not record.risk_approved and record.thesis_direction != "FLAT" else "")
        )

    # --- Review pass (step 6): complete any PENDING BUY whose holding
    # period has now elapsed, using real prices. Never touches decision-time
    # fields — see journal.append_outcome. ---
    rows = load_journal(journal_path)
    completed_this_run = 0
    for row in rows:
        ticker = row["ticker"]
        if not row.get("data_source", "").startswith("REAL"):
            # This row's own entry decision was made on SYNTHETIC (Phase 1)
            # data, on a completely different price scale from the REAL
            # market data fetched this run. Reviewing it against real exit
            # prices would produce a nonsense return (synthetic entry price
            # vs. real exit price) instead of a skip -- never mix scales.
            continue
        if row["action"] != "BUY" or row["outcome_status"] != "PENDING":
            continue  # nothing to review; avoids a wasted _entry_interval() parse below
        interval = _entry_interval(row["entry_date"])
        hist = histories.get((ticker, interval))
        bench = benchmarks.get(interval)
        if hist is None or bench is None:
            continue  # can't review without this (ticker, interval)'s real data this run
        try:
            updated = run_review_step(
                record=row,
                full_history=hist,
                holding_period_bars=_holding_period_bars_for(interval),
                journal_path=journal_path,
                taker_fee_bps=CONFIG.taker_fee_bps,
                slippage_bps=CONFIG.slippage_bps,
                benchmark_history=bench,
            )
        except Exception as exc:  # noqa: BLE001 — one bad/malformed row must not abort review for the rest
            print(f"[REVIEW ERROR] {ticker} {row['signal_date']}: {exc}")
            continue
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
