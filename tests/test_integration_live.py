"""
Manual/integration tests — these hit REAL external services and are NEVER
run as part of the normal test suite (`test_pipeline.py` / `test_phase2.py`
use synthetic data and mocked clients only).

- TestLiveDataFetch calls the real fetch_ohlcv() (yfinance, with a ccxt
  fallback) against the real network. Free, but requires outbound network
  access to Yahoo Finance and/or Coinbase.
- TestLiveThesisCall calls the real Anthropic API. Requires
  ANTHROPIC_KEY_FOR_TRADING to be set and makes one real, BILLED Claude API
  call.

Both classes are skipped by default. Run explicitly with:

    RUN_LIVE_INTEGRATION_TESTS=1 python3 -m unittest tests/test_integration_live.py -v

As of when this file was written, the sandbox used to build this project
had its outbound network access blocked by organization egress policy for
every market-data host tried (Yahoo Finance, Coinbase, Binance, Kraken) —
see the note at the top of src/data.py. TestLiveDataFetch has NOT been run
successfully in that environment; run it yourself once from an environment
with real network access before trusting fetch_ohlcv() in production.
"""

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

LIVE = os.environ.get("RUN_LIVE_INTEGRATION_TESTS") == "1"
_SKIP_REASON = "set RUN_LIVE_INTEGRATION_TESTS=1 to run tests against real external services"


@unittest.skipUnless(LIVE, _SKIP_REASON)
class TestLiveDataFetch(unittest.TestCase):
    def test_fetch_real_btc_data(self):
        from src.data import fetch_ohlcv, validate_ohlcv

        hist = fetch_ohlcv("BTC-USD", lookback_days=30, interval="1d")
        problems = validate_ohlcv(hist, "BTC-USD")
        self.assertEqual(problems, [], f"real BTC-USD data failed validation: {problems}")
        self.assertGreater(len(hist), 0)
        print(f"\nFetched {len(hist)} real bars, source={hist.attrs.get('data_source')}")
        print(hist.tail(3))

    def test_fetch_real_eth_data(self):
        from src.data import fetch_ohlcv, validate_ohlcv

        hist = fetch_ohlcv("ETH-USD", lookback_days=30, interval="1d")
        problems = validate_ohlcv(hist, "ETH-USD")
        self.assertEqual(problems, [], f"real ETH-USD data failed validation: {problems}")
        self.assertGreater(len(hist), 0)


@unittest.skipUnless(LIVE, _SKIP_REASON)
class TestLiveThesisCall(unittest.TestCase):
    def test_form_thesis_llm_real_call(self):
        """
        Uses SYNTHETIC bars so this test doesn't also depend on live data
        access -- only the LLM call itself is real here. Costs one real,
        billed claude-sonnet-5 call.
        """
        from src.data import generate_synthetic_ohlcv
        from src.thesis import form_thesis_llm

        hist = generate_synthetic_ohlcv("BTC-USD", n_bars=80, seed=42)
        thesis = form_thesis_llm("BTC-USD", hist)

        self.assertIn(thesis.direction, ("LONG", "FLAT"))
        self.assertTrue(0.0 <= thesis.confidence <= 1.0)
        self.assertTrue(thesis.reasoning.strip())
        self.assertTrue(thesis.source.startswith("LLM:"))
        print(f"\n{thesis.source} -> {thesis.direction} ({thesis.confidence:.2f}): {thesis.reasoning}")


if __name__ == "__main__":
    unittest.main()
