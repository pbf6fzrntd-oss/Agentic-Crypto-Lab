# Agentic Crypto Trading Workflow — Research Spec

Frozen specification for this experiment, written before any implementation.
Mirrors the discipline of the AI Treasure Hunt project this one branched from:
define the question, freeze the method, don't peek at results before the
rules are set.

## The Question

Does an AI trading agent that follows a structured, repeatable decision
workflow (gather data → form thesis → check risk/position sizing → decide →
log reasoning → review outcome) produce better risk-adjusted profitability on
intraday/daily-swing crypto trades than passive buy-and-hold on the same
asset(s), once volatility and transaction costs are accounted for?

## Why This Design

The "thesis formation" step is a **live LLM call**, not a fixed rule. That
choice has one big methodological consequence: a traditional historical
backtest cannot produce trustworthy evidence here, because the LLM may carry
training-data knowledge of what actually happened in any historical period it
is shown. This is a different, harder form of lookahead bias than
look-ahead-by-array-indexing — it can't be fixed by careful timestamp
handling.

So this project is explicitly split into two phases with different
evidentiary status:

### Phase 1 — Mechanical Dry Run (NOT evidence)

Purpose: prove the pipeline works end to end — data flows in, a thesis gets
formed, risk checks apply, a decision gets made, everything gets logged in
the right order, outcomes get scored against buy-and-hold.

Any "performance" numbers from Phase 1 are explicitly **non-evidentiary** and
must never be reported as if they demonstrate anything about the workflow's
real quality. They exist only to validate the plumbing.

### Phase 2 — Forward Paper Trading (the real test)

Purpose: the actual test of the hypothesis. The agent runs forward in real
time against data it could not have seen. Signals, thesis reasoning, and
decisions are logged before outcomes are known; outcomes are appended only
after they occur. This is the same prospective-journal discipline the
original SMA/ATR project adopted once its own backtest turned out fragile —
here it's the *only* valid evidence, not a fallback.

**Phase 2 is now implemented** (`src/run_paper_trading.py`, real
`fetch_ohlcv()` in `src/data.py`, real `form_thesis_llm()` in
`src/thesis.py`). It has logged **zero** decisions and completed **zero**
outcomes as of this writing — see "Reading Phase 2 output" below. Every
Phase 1 number remains explicitly non-evidentiary; nothing from Phase 1
carries over into the Phase 2 count.

#### Reading Phase 2 output

- Real evidence starts accumulating only from the moment
  `run_paper_trading.py` is first actually run on a schedule. Zero
  completed outcomes means zero evidence, not "evidence of no edge" — do
  not read an early, small, or empty sample as a result either way.
- The falsification bar (below) can only be checked once enough completed
  outcomes exist to say anything statistically meaningful — a handful of
  trades is not that bar.
- **Benchmark caveat:** `run_paper_trading.py` computes each trade's
  `excess_return` against an equal-weighted, real-data buy-and-hold basket
  of the fixed universe (BTC-USD + ETH-USD), not literally "the same
  instrument" — the pipeline's existing `excess_return` math (comparing the
  same ticker's own price on its own entry/exit dates) would trivially
  produce zero for every trade if the traded ticker were its own benchmark.
  See the docstring on `_build_benchmark()` in `run_paper_trading.py`. This
  was a judgment call made while implementing Phase 2, flagged to the
  researcher rather than decided silently — revisit it if a stricter
  per-instrument comparison is wanted; that would require changing
  `workflow.run_review_step`'s frozen math, not just the runner.
- **Data-fetch caveat:** `fetch_ohlcv()` was implemented and unit-tested
  with mocked responses, but the sandbox it was built in had no outbound
  network access to any market-data provider tried (Yahoo Finance,
  Coinbase, Binance, Kraken all returned policy-denied). It has not yet
  been exercised against a real response — run
  `RUN_LIVE_INTEGRATION_TESTS=1 python3 -m unittest tests/test_integration_live.py -v`
  once from an environment with real network access before relying on it.

## Frozen Parameters (Phase 1)

- **Universe:** BTC-USD, ETH-USD (fixed, small, liquid — chosen for data
  availability and to keep the dry run simple, not for any expected edge)
- **Benchmark:** Buy-and-hold on the same instrument over the same window
- **Horizon:** Intraday / daily-swing decisions (exact bar interval set in
  `config.py`)
- **Workflow steps (fixed order, do not reorder or skip):**
  1. `gather_data` — pull the most recent OHLCV bars available as of the
     decision timestamp only (no future bars)
  2. `form_thesis` — LLM call (stubbed in Phase 1) producing a directional
     view + stated reasoning
  3. `risk_check` — fixed position-sizing / risk rule, applied mechanically
  4. `decide` — combine thesis + risk check into a BUY / SELL / HOLD action
  5. `log` — append the full record (inputs, thesis, reasoning, decision) to
     the immutable journal *before* any outcome is known
  6. `review` — once the holding period has elapsed, append the realized
     outcome to the existing journal row; never rewrite the original fields

## What Would Prove This Wrong

If any apparent profitability edge over buy-and-hold disappears once
realistic volatility, fees, and slippage are applied, the workflow does not
have a validated edge. This is the researcher's own stated falsification
bar and should be checked explicitly whenever real (Phase 2) results exist —
never declare success from Phase 1 output.

## What This Project Is Not

- Not a live trading system. No real orders are placed anywhere in this
  codebase.
- Not investment advice. Nothing here should be read as a trade
  recommendation.
- Phase 1 results are not a backtest of a validated strategy — they are a
  pipeline smoke test only.
