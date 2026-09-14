# Agentic Crypto Trading Workflow — Phase 1 Scaffold

Research infrastructure for the question defined in `RESEARCH_SPEC.md`:
does a structured, repeatable agent decision workflow beat buy-and-hold on
crypto, once volatility and costs are accounted for?

**This is Phase 1 only — a mechanical pipeline smoke test using synthetic
data and a non-LLM stub "thesis" step. It produces no evidence about real
trading performance.** See `RESEARCH_SPEC.md` for why, and for the Phase 2
plan (forward paper trading) that will produce the real evidence.

## What's here

```
src/
  config.py       frozen parameters (universe, costs, sizing, horizon)
  data.py         data layer — synthetic generator (used now) + real-fetch
                  interface (NotImplementedError: no market-data network
                  access in this sandbox)
  thesis.py       step 2 "form_thesis" — interface + non-LLM stub
  risk.py         step 3 "risk_check" — fixed position-sizing rule
  journal.py      step 5/6 — append-only, immutable decision journal
  workflow.py     orchestrates the frozen 6-step sequence
  run_dry_run.py  Phase 1 entry point
tests/
  test_pipeline.py  validation tests (no-lookahead, immutability, ordering)
output/           journal + summary CSV land here
```

## Run it

```
python3 -m unittest discover -s tests -v   # 13 tests, all passing
python3 -m src.run_dry_run                  # runs the dry run end to end
```

## Known limitations of this scaffold

- **No market data access.** This environment cannot reach Yahoo Finance,
  Binance, or any other external data provider (blocked by network policy).
  `fetch_ohlcv()` in `data.py` is a real interface, unimplemented — wire it
  up from an environment with network access before Phase 2.
- **No LLM access for the thesis step.** `thesis.py`'s `stub_form_thesis` is
  a deterministic momentum heuristic standing in for the real LLM call. It
  exists only to exercise the pipeline. The real "form_thesis" — a live LLM
  call — is the actual subject of the research question and isn't wired up
  yet.
- **Synthetic price data.** Generated via a seeded random walk, tagged
  `data_source="SYNTHETIC"` everywhere it appears, specifically so it can't
  be confused with a real result.

## What's next (not built yet)

1. Wire `fetch_ohlcv()` to a real crypto data source, from an environment
   that can reach it.
2. Replace the stub thesis with a real LLM call, following the interface in
   `thesis.py` (`ThesisFn` in `workflow.py`).
3. Build the Phase 2 forward paper-trading runner: same six-step workflow,
   run on a schedule against live data, journaling signals before outcomes
   are known — this is where actual evidence starts accumulating.
4. Only after enough Phase 2 outcomes exist, check the falsification bar:
   does any apparent edge survive realistic volatility, fees, and slippage?
