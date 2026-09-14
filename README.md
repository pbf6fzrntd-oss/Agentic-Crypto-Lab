# Agentic Crypto Trading Workflow

Research infrastructure for the question defined in `RESEARCH_SPEC.md`:
does a structured, repeatable agent decision workflow beat buy-and-hold on
crypto, once volatility and costs are accounted for?

The project has two phases (see `RESEARCH_SPEC.md` for the full rationale):

- **Phase 1 — mechanical dry run (DONE, NOT evidence).** A pipeline smoke
  test on synthetic data with a non-LLM stub thesis step. Proves the
  plumbing works; says nothing about real trading quality.
- **Phase 2 — forward paper trading (DONE, real evidence starts here).**
  Real market data + a real Claude thesis call, run forward in time,
  journaled before outcomes are known. This is the only phase whose numbers
  are valid evidence — and as of this writing it has logged **zero**
  decisions, because it hasn't been run on a schedule yet. Zero is the
  correct starting point, not a bug.

## What's here

```
src/
  config.py            frozen parameters (universe, costs, sizing, horizon)
  data.py              data layer: generate_synthetic_ohlcv (Phase 1) +
                        fetch_ohlcv (Phase 2 — real, via yfinance with a
                        ccxt/Coinbase fallback)
  thesis.py            step 2 "form_thesis": stub_form_thesis (Phase 1,
                        non-LLM heuristic) + form_thesis_llm (Phase 2 —
                        real claude-sonnet-5 call)
  risk.py              step 3 "risk_check" — fixed position-sizing rule
  journal.py           step 5/6 — append-only, immutable decision journal
  workflow.py           orchestrates the frozen 6-step sequence (shared by
                        both phases — never changed between them)
  run_dry_run.py        Phase 1 entry point
  run_paper_trading.py  Phase 2 entry point — one pass per invocation, no
                        internal loop; invoke periodically (cron/scheduler/
                        manual). NEVER places a real order — see the
                        module docstring for the hard constraint.
tests/
  test_pipeline.py        Phase 1 tests (no-lookahead, immutability, ordering)
  test_phase2.py           Phase 2 tests — fetch_ohlcv and form_thesis_llm
                           with the network/API layer mocked; no real calls
  test_integration_live.py  Phase 2 tests against REAL services — skipped
                           unless RUN_LIVE_INTEGRATION_TESTS=1; costs real
                           money when it calls the LLM
output/           journal + summary CSV land here
```

## Run it

```
pip install -r requirements.txt
python3 -m unittest discover -s tests -v   # all mocked/synthetic tests, no cost, no network

python3 -m src.run_dry_run                 # Phase 1 — synthetic data, stub thesis

export ANTHROPIC_API_KEY=...               # required for Phase 2
python3 -m src.run_paper_trading           # Phase 2 — real data, real LLM call, one pass
```

## Known limitations

- **Phase 2 data fetch: confirmed working against live data (2026-09-14).**
  `fetch_ohlcv()` (yfinance, with a ccxt/Coinbase fallback) was originally
  built and unit-tested with mocked responses only, in a sandbox whose
  outbound network access was blocked for every market-data host tried. It
  has since been run for real: both `RUN_LIVE_INTEGRATION_TESTS=1 python3
  -m unittest tests/test_integration_live.py -v` and a live
  `run_paper_trading.py` invocation fetched and validated 400 real daily
  bars each for BTC-USD and ETH-USD from Yahoo Finance with no issues. The
  ccxt/Coinbase fallback still hasn't been exercised against a real
  response (yfinance hasn't failed yet, so it's never been triggered). If a
  validation check in `validate_ohlcv()` ever trips on real data, that's a
  real data-quality finding to bring back to the researcher, not something
  to loosen quietly.
- **Phase 2 LLM call: still blocked, now on missing credentials.** The same
  live run above failed at `form_thesis_llm()` for both tickers —
  `ANTHROPIC_API_KEY` wasn't set in that environment, so the Anthropic SDK
  couldn't authenticate. No decision was logged (the runner reports and
  skips rather than fabricating a thesis). Phase 2 still has zero logged
  decisions. Set `ANTHROPIC_API_KEY` before the next run for evidence to
  start accumulating.
- **A real bug was found and fixed while running the above.** The review
  pass used to match a journal row to any ticker in the freshly-fetched
  real history, without checking that row's own `data_source` — so it
  "completed" old Phase 1 SYNTHETIC rows using real BTC/ETH prices,
  fabricating absurd returns (a 760x BTC "return", two ~38x ETH
  "returns"). Caught before it was committed; fixed by
  `_is_reviewable_with_real_data()`, which restricts the review pass to
  rows whose `data_source` starts with `"REAL"`. Covered by a regression
  test in `tests/test_phase2.py`.
- **Cost.** Every `run_paper_trading.py` invocation that finds a new signal
  makes one real, billed `claude-sonnet-5` call per ticker (not per
  review). See the Phase 2 commit/PR description for the per-run cost
  estimate before scheduling this to run automatically.
- **Benchmark semantics.** Phase 2's `excess_return` is computed against an
  equal-weighted real-data buy-and-hold basket of the fixed universe, not
  literally the traded ticker's own price — see RESEARCH_SPEC.md's
  "Reading Phase 2 output" section for why, and flag it if you want the
  stricter per-instrument comparison RESEARCH_SPEC.md's wording could also
  support.

## What's next

Only after enough Phase 2 outcomes exist to say something statistically
meaningful, check the falsification bar from `RESEARCH_SPEC.md`: does any
apparent edge survive realistic volatility, fees, and slippage? Not before.
