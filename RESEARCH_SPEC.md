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
- **Horizon:** Intraday / daily-swing decisions — bar interval moved
  daily -> hourly -> back to daily, all on 2026-09-15 (see "Hourly
  cadence" and "Reverted to daily cadence" below). Exact bar interval set
  in `config.py`; currently `"1d"`.
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

### Hourly cadence (2026-09-15)

`Config.bar_interval` moved from `"1d"` to `"1h"`: `run_paper_trading.py`
now signals once per ticker per HOUR instead of once per day. Recorded
here for the same reason as every other change in this section — at the
time of this change, **19 real decisions had been logged and 0 outcomes
had completed** (still true when the run below added 20 more decisions,
still 0 completed). This is a widening of a frozen parameter made before
any real outcome existed to have tuned against, not a reaction to how the
workflow was performing.

What changed, and what deliberately did NOT:

- **`holding_period_bars`: 5 → 120.** Rescaled to keep the SAME real-world
  hold length (5 days) the original daily-bar design used — 120 hourly
  bars = 5 real days, matching the "~5 trading days" framing that's still
  hardcoded into `thesis.py`'s system prompt. This keeps the holding-period
  *hypothesis* unchanged; only the frequency of new signals changed. Both
  in one step would have made it impossible to attribute any observed
  effect to either change individually.
- **`CONTEXT_BARS` (thesis.py): left at 60, deliberately NOT rescaled.**
  Under daily bars this was ~60 days (~2 months) of price history shown to
  the model per call; under hourly bars it's now ~60 hours (~2.5 days) —
  a real, substantially shorter lookback window, not a preserved one.
  Scaling it to ~1440 bars to preserve the old real-world window was
  considered and rejected: it would have meant ~24x more input tokens
  (and ~24x the per-call cost) with no offsetting benefit established yet.
  If hourly-cadence results end up looking meaningfully different from
  daily-cadence ones, this shortened lookback is a real confound to keep
  in mind before attributing the difference to cadence alone.
- **`Config.phase2_lookback_days` (new field): 60.** Phase 2's real fetch
  now pulls 60 calendar days (~1440 hourly bars) per ticker per run — kept
  well within yfinance's proven real depth for hourly crypto data (tested
  live: ~99 days actually available) with headroom above the 60+120=180
  bars CONTEXT_BARS + holding_period_bars actually need. Split into its
  own field, separate from the original `lookback_days` (kept as-is,
  still Phase 1's synthetic bar count) — the two now mean genuinely
  different things at different scales and conflating them further would
  have made both harder to reason about.
- **`Config.max_daily_cost_usd`: $5.00 → $15.00.** Purely a headroom
  adjustment for ~20x more daily API calls (~20/day → ~480/day), not a
  loosened safety posture — see `cost_tracking.py` / the commit that added
  the cap. Real measured cost at hourly cadence: ~$0.0087/call, ~$0.17 for
  a full 20-ticker run, comfortably under the new cap.
- **A pre-existing gap in the portfolio-exposure cap was found and fixed
  alongside this change, not caused by it:** `run_paper_trading.py`'s
  gross-exposure tracking used to start at 0.0 every run, counting only
  that run's own newly-approved positions — silently blind to exposure
  from still-PENDING positions opened in *previous* runs. At daily cadence
  with a 5-bar hold this was a real but narrow gap (up to 5 stacked
  positions per ticker, 50% notional, could go uncounted); at hourly
  cadence with a 120-bar hold the same gap would have allowed up to 120
  stacked positions per ticker (1200% notional) to go uncounted — severe
  enough that it had to be fixed as part of this change rather than
  deferred. Gross exposure now starts from the sum of every currently-open
  (`PENDING`, `REAL:*`) position already in the journal. Verified live:
  the very first hourly run after this fix correctly blocked a
  fully-qualifying LONG signal (XLM-USD, confidence 0.58) once accumulated
  exposure — carried over from 4 pre-existing open positions plus 6 new
  approvals earlier in the same run — reached exactly the 100% cap.
- **Two accuracy bugs in what the model is actually told were found and
  fixed alongside this change:** `thesis.py`'s system prompt and its
  per-call user message both hardcoded the word "daily" ("recent daily
  OHLCV price data", "Realized daily volatility") regardless of the actual
  `bar_interval` — silently false, and materially misleading, the moment
  bars became hourly (a 2% per-bar stdev reads as mild volatility for
  daily bars, alarming for hourly ones). Both are now interval-aware.
  Separately, the per-call CSV sent to the model used to show only the
  bar's *date*, truncating the hour — meaning 24 different hourly bars on
  the same calendar day would have rendered as 24 identical-looking rows.
  Both are now full timestamps (also applied to `signal_date`/
  `entry_date`/`exit_date` in the journal itself, for the same reason:
  `_already_signaled`'s (ticker, date) uniqueness check and
  `run_review_step`'s index lookup would otherwise have silently
  collapsed every hour of a given day into one).
- **A real, unrelated data-layer bug was found and fixed while verifying
  this change:** `fetch_ohlcv()` used to slice `.tail(lookback_days)`
  treating `lookback_days` as a bar count, not a calendar-day count —
  correct by coincidence at "1d" (1 bar/day) but silently wrong at "1h"
  (tested live: asking for 90 calendar days of hourly bars returned only
  the last ~3.75 days). Fixed to convert calendar days to a bar count via
  the interval before slicing.
- **Phase 1 remains daily-only, deliberately un-migrated.**
  `generate_synthetic_ohlcv()` always simulates daily bars regardless of
  `Config.bar_interval` — a known, documented gap, not an oversight. Phase
  1 is a non-evidentiary plumbing smoke test; it no longer interval-matches
  Phase 2, but nothing about its validity as a smoke test depends on that
  match, and rebuilding it for arbitrary intervals was out of scope here.

### Universe correction (2026-09-15)

The 2026-09-14 "Universe expansion" note above was built from general
knowledge, not a live ranking — CoinGecko (and every other market-cap
ranking API tried) was blocked by this environment's network policy at
the time, so the 20 symbols were chosen by recognizability rather than
verified rank. Asked directly whether any of the 20 were actually
stablecoins, the answer was no (confirmed: none price near $1.00, all are
genuine `CRYPTOCURRENCY`-type, non-pegged assets) — but checking properly
surfaced that yfinance exposes real `marketCap` per ticker (not tried
before), which made an actual live ranking possible for the first time.
Recorded here per this document's own discipline: made with **59 real
decisions logged and 0 completed outcomes** — still true after the run
that applied this correction — before any result existed to have tuned
against.

Ranking ~35 candidates (the prior 20 plus known stablecoins, Lido Staked
ETH, Wrapped Bitcoin, and every plausible top-20 candidate not already in
the list) by real `marketCap` found the prior list had drifted from the
true top 20 in both directions:

- **Removed** (ranked outside the real top 20): `DOT-USD` (Polkadot,
  ~$1.7B), `ICP-USD` (~$1.5B), `ETC-USD` (~$1.2B), `ATOM-USD` (~$846M).
- **Added** (ranked inside the real top 20 but missing before):
  `XMR-USD` (Monero, ~$9.7B — rank ~8, higher than 12 of the 20 tickers
  already in the list), `TON11419-USD` (Toncoin, ~$4.5B), `HBAR-USD`
  (Hedera, ~$3.4B), `SUI20947-USD` (Sui, ~$2.95B).
- **Toncoin re-examined and included this time.** It was excluded during
  the original expansion for returning only 1 daily bar with a validation
  failure. Re-tested now at the interval Phase 2 actually trades on
  (`"1h"`, not `"1d"`): 1440 clean hourly bars, no validation problems.
  The original exclusion wasn't wrong for what was tested at the time; it
  just stopped being the right conclusion once the operating interval
  changed, and re-verifying against the interval actually in use rather
  than assuming the earlier daily-bar result still applied is what caught
  it.
- **Two pegged/derivative tokens deliberately excluded despite ranking in
  the raw top 20**, on the same principle RESEARCH_SPEC.md already states
  for stablecoins ("a pegged asset has no meaningful directional thesis...
  would dilute not test the hypothesis"): Lido Staked ETH (`STETH-USD`,
  tracks ETH 1:1 plus staking yield, ~$24.3B, would rank ~7) and Wrapped
  Bitcoin (`WBTC-USD`, tracks BTC 1:1, ~$9.1B, would rank ~10). Both are
  near-perfectly correlated with an asset already in the universe, so
  including them would double up on BTC/ETH exposure under a different
  ticker rather than add independent signal. This is a judgment call
  extending the stablecoin principle by analogy, not something explicitly
  asked for — flagged explicitly here rather than applied silently.

**A real operational gap was found and fixed while applying this
correction:** `run_paper_trading.py` fetched data for exactly
`Config.universe`, so dropping DOT/ICP/ETC/ATOM would have silently
orphaned `ICP-USD`'s one open (`PENDING`) position from before the
change — no data fetched for it ever again, so `run_review_step` would
never see it and it would stay `PENDING` forever, uncompleted, with no
error. Fixed: `main()` now fetches `Config.universe` UNION any ticker
with an already-open REAL position, and only signals fresh decisions on
`Config.universe` itself (a wind-down ticker is reviewed to completion,
never re-signaled). Verified live: the corrected run fetched and
validated all 20 new-universe tickers plus `ICP-USD` (printed
`[wind-down only, no longer in universe]`), opened no new `ICP-USD`
position, and left its existing one on track to complete on schedule.

### Historical validation ("Phase 1.5", 2026-09-15)

Added `src/run_historical_validation.py`: the same frozen six-step
workflow, fed REAL 12-month daily OHLCV history (`fetch_ohlcv()` / Yahoo
Finance — the same function Phase 2 uses) instead of Phase 1's synthetic
random walk, but still using `stub_form_thesis()` — the same non-LLM
heuristic Phase 1 uses, NOT `form_thesis_llm()`. It never imports
`form_thesis_llm` or anything from `cost_tracking.py`, and never reads
`ANTHROPIC_KEY_FOR_TRADING` — enforced by a test that parses the module's
own import statements, not just observed behavior. Writes to its own
`Config.historical_journal_path`, a third journal entirely separate from
both `journal_path` (Phase 2 real evidence) and `phase1_journal_path`
(Phase 1 synthetic) — real prices, fake thesis, and it must never be
mistaken for either of the other two.

**This is explicitly NOT evidence, and does not speed up the
falsification check, no matter how much real price history it runs
against.** The reason real evidence is restricted to live, forward-only
Phase 2 in the first place (see "Why This Design" above) is that a
historical backtest of the *LLM thesis step specifically* can't be
trusted — the model may carry training-data knowledge of what actually
happened on any historical date it's shown, a form of lookahead bias no
amount of careful timestamp handling fixes. This script sidesteps that
problem by definition (it never asks the LLM anything), but that also
means it can only test the MECHANICAL parts of the pipeline — data
quality, cost model, no-lookahead enforcement, benchmark construction —
against real market history, plus show what a purely mechanical (non-LLM)
momentum rule would have done. Neither answers the actual research
question. Its numbers are exactly as non-evidentiary as Phase 1's
synthetic-data numbers — real prices under a fake thesis, instead of fake
prices under a fake thesis.

Verified live against the real universe: 17 of 20 tickers had clean
12-month daily history (`SOL-USD`, `TON11419-USD`, and `SUI20947-USD`
each hit a real one-bar data-quality issue and were correctly skipped by
`validate_ohlcv()`, same as this pipeline already does live — not a bug
in this script). 6,103 decisions, 2,150 BUY, 2,139 completed outcomes,
mean net-of-cost return of the mechanical stub over real 2025-2026 crypto
price history: **-1.10%** — plausible for a naive momentum rule after
15bps round-trip costs, and a useful sanity check that the pipeline
behaves sensibly against a full year of real data, but again: a fact
about a mechanical baseline, not about the LLM. Does not apply the
portfolio-level gross-exposure cap `run_paper_trading.py` does — mirrors
Phase 1's simpler per-ticker-independent backfill exactly, since
date-synchronized cap-aware backfilling across 20 tickers was out of
scope for a script whose numbers are non-evidentiary either way.

### Reverted to daily cadence (2026-09-15)

`Config.bar_interval` moved back `"1h"` -> `"1d"`, less than 24 hours
after the "Hourly cadence" change above. Made with **77 real decisions
logged and 0 completed outcomes** — still true after applying the
reversion — before any result existed to have tuned against, same as
every other change in this section.

**Why**: the portfolio-exposure cap (`Config.max_gross_exposure_fraction`
= 100%, `position_size_fraction` = 10% per name) creates a hard ceiling
of 10 concurrently-open positions, each held for the same real-world 5
days regardless of how often signals are evaluated. That means steady-
state evidence throughput is capped at roughly 10 positions / 5 days ≈ 2
completed outcomes per day, *independent of signal frequency* — hourly
signaling fills the queue faster, it does not drain it faster. Discussed
explicitly with the researcher: hourly cost ~20x more (~$3.84/day vs.
~$0.17/day measured live) for no faster path to a completed-outcome
count, so daily cadence was chosen as strictly better on the only axis
that mattered (evidence per dollar), with no offsetting benefit to
hourly identified. Revisiting hourly (or something between) remains
worth doing later as its own deliberate research question — e.g. once
daily-cadence evidence exists as a baseline to compare a higher-frequency
variant against — just not as a way to reach the SAME falsification bar
faster.

**A real gap surfaced and fixed while reverting**: 6 of the 10 open
positions at the time (`XRP-USD`, `SOL-USD`, `AVAX-USD`, `LINK-USD`,
`NEAR-USD` x2, `UNI7083-USD`) were entered at hourly precision (e.g.
`entry_date="2026-09-15 01:00:00"`) while `bar_interval="1h"`. Simply
flipping `bar_interval` back to `"1d"` would have fetched only daily
bars going forward — none of which land on that exact hourly timestamp —
silently stranding those 6 positions `PENDING` forever, the same failure
shape as the ticker-removal gap fixed in "Universe correction" above,
just triggered by an interval change instead of a universe change.
Generalized the fix instead of patching this one instance:
`run_paper_trading.py` now infers which interval each open position was
actually entered under (`_entry_interval()`, from whether its
`entry_date` lands on midnight or a real hour — exact for every interval
this project has used) and fetches each `(ticker, interval)` pair that's
actually needed — every universe ticker at the CURRENT interval, plus
every open position's own ticker at ITS entry interval — rather than
just `CONFIG.universe x CONFIG.bar_interval`. `Config.holding_period_bars`
is similarly only valid for `Config.bar_interval` specifically (it's a
bar count, not a calendar-time invariant: 120 hourly bars and 5 daily
bars are both "5 real days"), so a new `_holding_period_bars_for()`
derives the equivalent bar count at any other interval via the real-day
count both express, rather than hardcoding a second magic number that
could drift out of sync with `Config.holding_period_bars`. This is now
fully general — robust to `bar_interval` changing again in the future,
not just a fix for this specific transition. Verified live: the reverted
run correctly fetched all 20 universe tickers at `"1d"` (2 hit real
one-bar data-quality issues, correctly skipped, same as always) plus the
6 legacy positions at their own `"1h"`, printed `[wind-down only]` for
each, logged 18 new daily-precision decisions, and produced zero
`[REVIEW ERROR]` lines.

### Duplicate-signal guard hardened (2026-09-15)

Found while auditing the journal before letting the daily Routine run
unattended on real API calls, **before any further result existed to
have tuned against**: 77 real decisions logged, 0 completed outcomes,
same as the section above.

**What was found**: 14 tickers have TWO real, independently-billed
decisions logged for the same real calendar day, 2026-09-13 — one with
`signal_date="2026-09-13"` (bare date), one with
`signal_date="2026-09-13 00:00:00"` (full timestamp). These name the
exact same price bar. `_already_signaled()`, the idempotency guard that
exists specifically to stop this script from re-signaling (and
re-billing) a `(ticker, signal_date)` pair it's already logged, compared
`signal_date` as a **raw string** — so the format mismatch made it blind
to the collision.

**Root cause**: the bare-date format predates the fix noted in
`workflow.py` (see its `entry_date`/`signal_date` comment) that switched
`signal_date`/`entry_date` from `str(ts.date())` to `str(ts)` specifically
so hourly bars on the same calendar date wouldn't collapse into one
string. That fix was correct and is still needed — but it only changed
what NEW rows look like; it did nothing to protect a later run's
`_already_signaled()` check against OLD rows already sitting in the
journal in the pre-fix format. The 2026-09-13 rows are exactly that: one
run under the old format, a later run (after the fix landed) recomputing
the same calendar day under the new format and not recognizing it as a
duplicate.

**Impact, checked directly against the journal**: zero exposure/PnL
corruption — no ticker has two `BUY` rows for 2026-09-13 (the would-be
second `BUY`s for `TRX-USD`/`NEAR-USD`/`LTC-USD`/`HBAR-USD` all came back
`HOLD` on the second pass, either genuinely `FLAT` or blocked by the
exposure cap, since real LLM calls aren't deterministic across separate
invocations). What it DOES mean: ~14 duplicate real, billed LLM calls
happened that day (~$0.12 wasted, one-time), and `total_real_decisions`
in every report/dashboard is **inflated by 14** for as long as those rows
exist. The journal is append-only/immutable by design (see "Journal
separation" above) — these duplicate rows are NOT deleted or edited; this
note is the record of what they are and why, the same policy already
applied to other known data quirks in this file.

**Fix**: `_already_signaled()` now parses both sides through
`pd.Timestamp` before comparing, instead of comparing raw strings. This
is a read-time fix — it makes the guard correctly recognize a duplicate
regardless of which string format either the stored row or the freshly
computed candidate happens to be in, closing this specific class of bug
permanently rather than just for the one format pair that happened to
collide here. Regression test added
(`test_phase2.py::test_already_signaled_matches_across_date_string_formats`).
Full suite: 83 passed, 3 skipped.

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
