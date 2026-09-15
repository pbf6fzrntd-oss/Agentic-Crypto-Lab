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
  risk.py              step 3 "risk_check" — fixed position-sizing rule +
                        a portfolio-level gross-exposure cap
  journal.py           step 5/6 — append-only, immutable decision journal
                        (atomic writes, locked against concurrent runs);
                        append_decisions()/append_outcomes() are batched
                        variants for a caller logging many records at once
  cost_tracking.py     cost telemetry + hard daily-spend circuit breaker
                        for form_thesis_llm()'s real API calls
  workflow.py           orchestrates the frozen 6-step sequence (shared by
                        both phases — never changed between them)
  run_dry_run.py        Phase 1 entry point
  run_paper_trading.py  Phase 2 entry point — one pass per invocation, no
                        internal loop; invoke periodically (cron/scheduler/
                        manual, matching Config.bar_interval — hourly as of
                        2026-09-15). NEVER places a real order — see the
                        module docstring for the hard constraint.
  generate_report.py    reads the REAL journal only, writes a human-
                        readable status report (Config.report_path)
  dashboard_data.py     emits the same report data as one JSON blob, plus
                        open-positions/recent-decisions lists — what the
                        published dashboard artifact (see below) refreshes
                        itself from
  run_historical_validation.py  "Phase 1.5" — REAL 12mo daily price
                        history (Yahoo Finance) but the NON-LLM
                        stub_form_thesis, never the Anthropic API. NOT
                        evidence, does not speed up the falsification
                        check — see RESEARCH_SPEC.md's "Historical
                        validation" note for exactly why.
tests/
  test_pipeline.py        Phase 1 tests (no-lookahead, immutability, ordering)
  test_phase2.py           Phase 2 tests — fetch_ohlcv and form_thesis_llm
                           with the network/API layer mocked; no real calls
  test_run_paper_trading.py  main()-level integration tests: the review pass
                           never mixes SYNTHETIC/REAL data sources, and a
                           re-run makes no duplicate (billed) LLM calls
  test_run_dry_run.py     Phase 1's journal-separation guard: never touches
                           a real-evidence journal at a different path
  test_run_historical_validation.py  asserts run_historical_validation.py
                           never imports form_thesis_llm/cost_tracking and
                           never touches the real journal
  test_journal_safety.py  atomic-write, concurrent-locking, and batched-
                           append tests for journal.py
  test_cost_tracking.py   cost-estimation and daily-cap tests for
                           cost_tracking.py
  test_generate_report.py    report-computation tests, incl. the "not
                           enough data for a read" framing
  test_dashboard_data.py  tests for the dashboard's extra (non-report) data
  test_integration_live.py  Phase 2 tests against REAL services — skipped
                           unless RUN_LIVE_INTEGRATION_TESTS=1; costs real
                           money when it calls the LLM
output/
  decision_journal.jsonl        Phase 2's REAL-evidence journal ONLY —
                                 the only file Phase 2's evidence count is
                                 ever read from
  phase1_dry_run_journal.jsonl  Phase 1's own journal — deleted and
                                 regenerated on every dry-run invocation;
                                 entirely separate from the file above (see
                                 RESEARCH_SPEC.md's "Journal separation")
  phase1_dry_run_summary.csv    Phase 1 smoke-test summary CSV
  historical_validation_journal.jsonl  run_historical_validation.py's own
                                 journal — real prices, stub thesis, NOT
                                 evidence; a third category, separate from
                                 both files above
  historical_validation_summary.csv    its summary CSV
  llm_cost_log.jsonl            one row per real form_thesis_llm() call —
                                 tokens used + estimated USD cost; read by
                                 cost_tracking.py to enforce the daily cap
  phase2_daily_report.md        generate_report.py's output — what the
                                 REAL journal actually shows, regenerated
                                 daily by a scheduled Routine
```

## Scheduled automation

Two Claude Code Remote Routines run this project unattended (set up
2026-09-14/15; see a session's Routines list to inspect/change them):

- **Phase 2 hourly trading** — fires hourly, runs `run_paper_trading.py`
  in a fresh session, commits any new `decision_journal.jsonl` rows back
  to this branch (real evidence must survive container reclamation).
- **Phase 2 daily report** — fires once daily, runs `generate_report.py`,
  commits `phase2_daily_report.md`, and refreshes a published dashboard
  artifact (a `Phase 2 Ledger` HTML page) with the same data via
  `dashboard_data.py`. Sends a push/email summary either way, flagged
  `ATTENTION NEEDED` if anything errored.

## Run it

```
pip install -r requirements.txt
python3 -m unittest discover -s tests -v   # all mocked/synthetic tests, no cost, no network

python3 -m src.run_dry_run                 # Phase 1 — synthetic data, stub thesis

export ANTHROPIC_KEY_FOR_TRADING=...       # required for Phase 2
python3 -m src.run_paper_trading           # Phase 2 — real data, real LLM call, one pass

python3 -m src.run_historical_validation   # "Phase 1.5" — real 12mo data, stub thesis,
                                            # NEVER touches ANTHROPIC_KEY_FOR_TRADING or the
                                            # API. NOT evidence — see RESEARCH_SPEC.md.
```

## Known limitations

- **Phase 2 data fetch has since been exercised against live data
  (2026-09-14) and works.** The note that used to be here said this was
  unproven because the original build sandbox's egress policy blocked
  every market-data host tried. That was environment-specific, not a
  property of the code: run from an environment with real network access
  (as this project now has been, repeatedly), `fetch_ohlcv()` correctly
  fetches real BTC-USD/ETH-USD/etc. data via yfinance. If you're running
  from a *new* restricted sandbox, re-verify with
  `RUN_LIVE_INTEGRATION_TESTS=1 python3 -m unittest tests/test_integration_live.py -v`
  before trusting it there. If a validation check in `validate_ohlcv()`
  trips on real data that never tripped on synthetic data (this has
  happened — a single bad bar from the data provider), that's a real
  data-quality finding to bring back to the researcher, not something to
  loosen quietly.
- **Cost.** Every `run_paper_trading.py` invocation that finds a new signal
  makes one real, billed `claude-sonnet-5` call per ticker (not per
  review) — at `output_config={"effort": "low"}`, ~$0.0087/call measured
  live at hourly cadence (`Config.bar_interval = "1h"` as of 2026-09-15;
  see RESEARCH_SPEC.md's "Hourly cadence" note), i.e. ~$0.17 for a full
  20-ticker run and well under $5/day even run hourly (~480 calls/day).
  `thesis.py` enforces a hard daily spend cap (`Config.max_daily_cost_usd`,
  $15.00) via `cost_tracking.py` regardless — see `output/llm_cost_log.jsonl`
  for the running total.
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
