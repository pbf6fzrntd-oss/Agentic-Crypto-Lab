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
- **Data-fetch caveat — RESOLVED 2026-09-14.** `fetch_ohlcv()` was
  implemented and unit-tested with mocked responses, but the sandbox it was
  built in had no outbound network access to any market-data provider tried
  (Yahoo Finance, Coinbase, Binance, Kraken all returned policy-denied). It
  has now been run once from an environment with real network access:
  `RUN_LIVE_INTEGRATION_TESTS=1 python3 -m unittest tests/test_integration_live.py -v`
  passed against live Yahoo Finance data for both BTC-USD and ETH-USD
  (400 real daily bars each fetched and validated by `run_paper_trading.py`
  too). The yfinance path works as documented; the ccxt/Coinbase fallback
  remains unexercised against a real response (yfinance never failed, so it
  was never triggered).
- **LLM-call caveat — still blocked, different reason.** The first real
  invocation of `run_paper_trading.py` (2026-09-14) got past data-fetch
  cleanly but failed at `form_thesis_llm()` for both tickers with
  "Could not resolve authentication method" — that sandbox had no
  `ANTHROPIC_API_KEY` configured for direct SDK use. No decision was
  logged (the runner correctly skips-and-reports rather than fabricating a
  thesis on this failure), so the journal is untouched. Phase 2 still has
  **zero** logged decisions and **zero** completed outcomes as of this
  writing. Run again from an environment with `ANTHROPIC_API_KEY` set
  before Phase 2 evidence can start accumulating.
- **Bug found and fixed while running the above (2026-09-14):** the review
  pass in `run_paper_trading.py` matched any journal row for a ticker
  present in that run's freshly-fetched real history — including Phase 1
  rows with `data_source == "SYNTHETIC"` — and "completed" them using real
  BTC/ETH prices. Because synthetic bars are priced around $100 and real
  BTC/ETH bars are not, this fabricated outcomes like a 760x BTC-USD return
  and two ~38x ETH-USD returns on old Phase 1 rows before the bug was
  caught. It was caught before being committed (the corrupted journal was
  reverted, never pushed) and is now fixed: the review pass only considers
  rows whose `data_source` starts with `"REAL"` (see
  `_is_reviewable_with_real_data()` in `run_paper_trading.py`, covered by a
  regression test in `tests/test_phase2.py`). Phase 1 SYNTHETIC rows now
  correctly stay PENDING forever under this runner, as intended.

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
