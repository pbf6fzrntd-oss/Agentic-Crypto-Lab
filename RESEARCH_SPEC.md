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

**Phase 2 is now implemented and running** (`src/run_paper_trading.py`,
real `fetch_ohlcv()` in `src/data.py`, real `form_thesis_llm()` in
`src/thesis.py`). As of 2026-09-14 it has logged **19** real decisions
(all HOLD/FLAT or newly-opened BUY so far) and completed **zero**
outcomes — the earliest BUYs haven't reached their 5-bar holding period
yet. Zero completed outcomes is still the correct state to be in this
early; see "Reading Phase 2 output" below for how to read this count as
it grows. Every Phase 1 number remains explicitly non-evidentiary; nothing
from Phase 1 carries over into the Phase 2 count.

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
  of the fixed universe (the top-20 tuple in `config.py`), not literally "the same
  instrument" — the pipeline's existing `excess_return` math (comparing the
  same ticker's own price on its own entry/exit dates) would trivially
  produce zero for every trade if the traded ticker were its own benchmark.
  See the docstring on `_build_benchmark()` in `run_paper_trading.py`. This
  was a judgment call made while implementing Phase 2, flagged to the
  researcher rather than decided silently — revisit it if a stricter
  per-instrument comparison is wanted; that would require changing
  `workflow.run_review_step`'s frozen math, not just the runner.
- **Data-fetch caveat (resolved 2026-09-14):** `fetch_ohlcv()` was
  originally implemented and unit-tested with mocked responses only — the
  sandbox it was built in had no outbound network access to any
  market-data provider tried (Yahoo Finance, Coinbase, Binance, Kraken all
  returned policy-denied), so it had never been exercised against a real
  response. It has since been run repeatedly from an environment with real
  network access (the one this project now runs Phase 2 from) and works
  correctly against real yfinance data. If run from a *different*,
  possibly-restricted environment, re-verify first with
  `RUN_LIVE_INTEGRATION_TESTS=1 python3 -m unittest tests/test_integration_live.py -v`.

## Frozen Parameters (Phase 1)

- **Universe:** the top 20 non-stablecoin cryptocurrencies by market cap
  (expanded from BTC-USD, ETH-USD on 2026-09-14 — see "Universe expansion"
  below), fixed and liquid — chosen for data availability, not for any
  expected edge. The exact tuple lives in `config.py`.
- **Benchmark:** Buy-and-hold on the same instrument over the same window
- **Horizon:** Intraday / daily-swing decisions (exact bar interval set in
  `config.py`)
- **Workflow steps (fixed order, do not reorder or skip):**
  1. `gather_data` — pull the most recent OHLCV bars available as of the
     decision timestamp only (no future bars)
  2. `form_thesis` — LLM call (stubbed in Phase 1) producing a directional
     view + stated reasoning
  3. `risk_check` — fixed position-sizing / risk rule, applied mechanically
     (as of 2026-09-14, also enforces a fixed portfolio-level gross-exposure
     cap across the whole universe in a single run — see "Universe
     expansion" below for why)
  4. `decide` — combine thesis + risk check into a BUY / SELL / HOLD action
  5. `log` — append the full record (inputs, thesis, reasoning, decision) to
     the immutable journal *before* any outcome is known
  6. `review` — once the holding period has elapsed, append the realized
     outcome to the existing journal row; never rewrite the original fields

### Universe expansion (2026-09-14)

The universe was widened from the original (BTC-USD, ETH-USD) pair to the
top 20 non-stablecoin cryptocurrencies by market cap. Recorded here, per
this document's own discipline ("define the question, freeze the method,
don't peek at results before the rules are set"), so this change's timing
relative to the evidence is auditable rather than asserted:

- **At the time of this change, Phase 2 had logged 2 real decisions and
  completed ZERO real outcomes.** There was no result yet to have peeked
  at or tuned against — this is a widening of the frozen parameter set, not
  a post-hoc adjustment made in response to how the workflow was
  performing.
- **Stablecoins (USDT, USDC, DAI, ...) are deliberately excluded.** A
  pegged asset has no meaningful directional thesis for `form_thesis_llm`
  to form — including them wouldn't test the hypothesis, just dilute it.
- **Each symbol was verified, not guessed**, against this project's own
  `fetch_ohlcv()` before being added to `config.py`: real data returned,
  `validate_ohlcv()` clean, and — critically — its Yahoo Finance `longName`
  checked to confirm the ticker actually resolves to the intended asset.
  That check caught two symbol collisions that would otherwise have put the
  wrong asset in the universe silently: plain `TON-USD` resolves to an
  unrelated project called "TON Token", not Toncoin (the real Toncoin is
  `TON11419-USD`); plain `ARB-USD` resolves to "ARbit", not Arbitrum (the
  real Arbitrum token is `ARB11841-USD`). Toncoin was ultimately left out of
  the final 20 anyway — even at its correct symbol, Yahoo returned only 1
  daily bar with a validation failure over a 30-day check window, failing
  this project's own "chosen for data availability" bar for universe
  membership, the same standard BTC-USD/ETH-USD were originally chosen by.
- **Cost and risk scale with universe size.** Going from 2 to 20 tickers is
  a ~10x increase in daily billed `form_thesis_llm` calls (still cheap at
  `output_config={"effort": "low"}`, but not free indefinitely). More
  importantly, `risk_check`'s fixed 10% per-position sizing was previously
  safe by construction (2 positions × 10% ≤ 20% of notional, always); at 20
  tickers, an uncapped run could approve up to 200% of notional if every
  name signaled LONG the same day (e.g. a market-wide rally). A fixed
  portfolio-level gross-exposure cap (`Config.max_gross_exposure_fraction`,
  default 1.0 = 100%) was added to `risk_check` alongside this change for
  that reason — mechanical and universe-size-independent, not tuned against
  any observed result, consistent with this project's position-sizing
  discipline.

### Journal separation (2026-09-14)

Phase 1 (`run_dry_run.py`) and Phase 2 (`run_paper_trading.py`) used to
share a single journal file (`Config.journal_path`). That was a latent
risk this document should have called out from the start: `run_dry_run.py`
unconditionally deletes and regenerates its journal on every run (by
design — Phase 1 is a repeatable smoke test, not a log worth preserving),
and because both phases wrote to the same path, re-running Phase 1 at any
point after Phase 2 had accumulated real evidence would have silently
destroyed that evidence.

Fixed by giving Phase 1 its own file, `Config.phase1_journal_path`
(`output/phase1_dry_run_journal.jsonl`), entirely separate from
`Config.journal_path` (`output/decision_journal.jsonl`), which is now
Phase 2's real-evidence journal exclusively. The existing committed
journal was split along its `data_source` field to migrate cleanly with
no data loss: 788 `SYNTHETIC` rows moved to the new Phase 1 file, the 19
existing `REAL:*` rows stayed in `decision_journal.jsonl`. `run_dry_run.py`
also now refuses (raises, rather than silently deleting) if the file at
`phase1_journal_path` ever contains a `REAL:*` row, as a second line of
defense in case that path is ever misconfigured.

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
