"""
Phase 2 tests — real-data fetch, real LLM thesis call, and the paper-trading
runner's helper functions.

Everything in this file runs WITHOUT hitting any real network or external
API: fetch_ohlcv() is tested by mocking yfinance/ccxt at the point this
project calls them, and form_thesis_llm() is tested by mocking the Anthropic
client. For tests that DO hit real services, see
tests/test_integration_live.py (skipped unless explicitly requested).

Run with: python3 -m pytest tests/ -v   (or python3 -m unittest discover)
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from src.data import fetch_ohlcv, generate_synthetic_ohlcv
from src.thesis import MIN_BARS_FOR_LLM_THESIS, form_thesis_llm
from src.run_paper_trading import (
    _already_signaled,
    _build_benchmark,
    _is_reviewable_with_real_data,
    _select_signal_date,
)


def _fake_yf_history(n_bars=30, tz_aware=True):
    dates = pd.date_range(end=pd.Timestamp.now(tz="UTC" if tz_aware else None), periods=n_bars, freq="D")
    df = pd.DataFrame(
        {
            "Open": [100.0 + i for i in range(n_bars)],
            "High": [101.0 + i for i in range(n_bars)],
            "Low": [99.0 + i for i in range(n_bars)],
            "Close": [100.5 + i for i in range(n_bars)],
            "Volume": [1_000_000.0] * n_bars,
        },
        index=dates,
    )
    return df


class TestFetchOhlcvYfinance(unittest.TestCase):
    def test_success_returns_required_columns_and_strips_tz(self):
        fake_hist = _fake_yf_history(30, tz_aware=True)
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = fake_hist

        with patch("yfinance.Ticker", return_value=mock_ticker):
            df = fetch_ohlcv("BTC-USD", lookback_days=30, interval="1d")

        self.assertListEqual(list(df.columns), ["Open", "High", "Low", "Close", "Volume"])
        self.assertIsNone(df.index.tz)
        self.assertEqual(df.attrs["data_source"], "REAL:yfinance")
        self.assertEqual(df.attrs["ticker"], "BTC-USD")

    def test_falls_back_to_ccxt_when_yfinance_empty(self):
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame()  # empty -> triggers fallback

        fake_bars = [
            [int(pd.Timestamp("2026-01-01").timestamp() * 1000), 100.0, 101.0, 99.0, 100.5, 1000.0],
            [int(pd.Timestamp("2026-01-02").timestamp() * 1000), 100.5, 102.0, 100.0, 101.5, 1100.0],
        ]
        mock_exchange = MagicMock()
        mock_exchange.fetch_ohlcv.return_value = fake_bars
        mock_exchange.parse8601.return_value = 0

        with patch("yfinance.Ticker", return_value=mock_ticker), \
             patch("ccxt.coinbase", return_value=mock_exchange):
            df = fetch_ohlcv("BTC-USD", lookback_days=30, interval="1d")

        self.assertEqual(df.attrs["data_source"], "REAL:ccxt:coinbase")
        self.assertEqual(len(df), 2)

    def test_raises_when_both_sources_fail(self):
        with patch("yfinance.Ticker", side_effect=RuntimeError("network down")), \
             patch("ccxt.coinbase", side_effect=RuntimeError("also down")):
            with self.assertRaises(RuntimeError):
                fetch_ohlcv("BTC-USD", lookback_days=30, interval="1d")


class TestFormThesisLlm(unittest.TestCase):
    def test_insufficient_history_returns_flat_without_calling_api(self):
        hist = generate_synthetic_ohlcv("BTC-USD", n_bars=MIN_BARS_FOR_LLM_THESIS - 1, seed=1)
        with patch("anthropic.Anthropic") as mock_anthropic_cls:
            thesis = form_thesis_llm("BTC-USD", hist)
        mock_anthropic_cls.assert_not_called()
        self.assertEqual(thesis.direction, "FLAT")
        self.assertEqual(thesis.confidence, 0.0)

    def test_parses_tool_call_response_into_thesis(self):
        hist = generate_synthetic_ohlcv("BTC-USD", n_bars=80, seed=2)

        fake_tool_block = MagicMock()
        fake_tool_block.type = "tool_use"
        fake_tool_block.input = {
            "direction": "LONG",
            "confidence": 0.73,
            "reasoning": "Price grinding higher over the window with low realized vol.",
        }
        fake_response = MagicMock()
        fake_response.content = [fake_tool_block]
        fake_response.stop_reason = "tool_use"

        mock_client = MagicMock()
        mock_client.messages.create.return_value = fake_response

        with patch("anthropic.Anthropic", return_value=mock_client) as mock_anthropic_cls:
            thesis = form_thesis_llm("BTC-USD", hist)

        mock_anthropic_cls.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args.kwargs
        self.assertEqual(call_kwargs["tool_choice"], {"type": "tool", "name": "record_thesis"})
        self.assertEqual(len(call_kwargs["messages"]), 1)

        self.assertEqual(thesis.direction, "LONG")
        self.assertAlmostEqual(thesis.confidence, 0.73)
        self.assertIn("grinding higher", thesis.reasoning)
        self.assertTrue(thesis.source.startswith("LLM:"))

    def test_missing_tool_use_block_raises(self):
        hist = generate_synthetic_ohlcv("BTC-USD", n_bars=80, seed=3)

        text_block = MagicMock()
        text_block.type = "text"
        fake_response = MagicMock()
        fake_response.content = [text_block]
        fake_response.stop_reason = "end_turn"

        mock_client = MagicMock()
        mock_client.messages.create.return_value = fake_response

        with patch("anthropic.Anthropic", return_value=mock_client):
            with self.assertRaises(RuntimeError):
                form_thesis_llm("BTC-USD", hist)

    def test_context_is_limited_to_context_bars(self):
        # Sends only the most recent CONTEXT_BARS rows, not the full history,
        # even when given a much longer no-lookahead-safe window.
        hist = generate_synthetic_ohlcv("BTC-USD", n_bars=400, seed=4)

        fake_tool_block = MagicMock()
        fake_tool_block.type = "tool_use"
        fake_tool_block.input = {"direction": "FLAT", "confidence": 0.2, "reasoning": "r"}
        fake_response = MagicMock()
        fake_response.content = [fake_tool_block]
        fake_response.stop_reason = "tool_use"

        mock_client = MagicMock()
        mock_client.messages.create.return_value = fake_response

        with patch("anthropic.Anthropic", return_value=mock_client):
            form_thesis_llm("BTC-USD", hist)

        user_message = mock_client.messages.create.call_args.kwargs["messages"][0]["content"]
        # 400 bars sent, 60 (CONTEXT_BARS) expected -> the line count of the
        # CSV block should reflect 60 rows, not 400.
        csv_lines = [l for l in user_message.split("\n") if l and l[0].isdigit()]
        self.assertEqual(len(csv_lines), 60)


class TestPaperTradingRunnerHelpers(unittest.TestCase):
    def test_select_signal_date_is_second_to_last_bar(self):
        hist = generate_synthetic_ohlcv("BTC-USD", n_bars=30, seed=5)
        signal_date = _select_signal_date(hist)
        self.assertEqual(signal_date, hist.index[-2])
        # Its "next bar" (the actual last fetched bar) must already exist.
        self.assertEqual(hist.index[-1], hist.loc[signal_date:].index[-1])

    def test_already_signaled_detects_existing_ticker_date_pair(self):
        rows = [{"ticker": "BTC-USD", "signal_date": "2026-01-05"}]
        self.assertTrue(_already_signaled(rows, "BTC-USD", "2026-01-05"))
        self.assertFalse(_already_signaled(rows, "BTC-USD", "2026-01-06"))
        self.assertFalse(_already_signaled(rows, "ETH-USD", "2026-01-05"))

    def test_synthetic_rows_are_never_reviewable_with_real_data(self):
        # Regression test: a Phase 1 SYNTHETIC decision must never be
        # reviewed against Phase 2 REAL price history -- the price scales
        # are unrelated, so matching entry_date strings across them would
        # fabricate a nonsense outcome (see the bug this guards against,
        # found by actually running the Phase 2 runner against real data:
        # it "completed" old synthetic BTC/ETH rows with real BTC/ETH exit
        # prices, producing e.g. a 700x fabricated return).
        self.assertFalse(_is_reviewable_with_real_data({"data_source": "SYNTHETIC"}))
        self.assertTrue(_is_reviewable_with_real_data({"data_source": "REAL:yfinance"}))
        self.assertTrue(_is_reviewable_with_real_data({"data_source": "REAL:ccxt:coinbase"}))
        self.assertFalse(_is_reviewable_with_real_data({}))

    def test_build_benchmark_is_not_identical_to_any_single_ticker(self):
        btc = generate_synthetic_ohlcv("BTC-USD", n_bars=50, seed=6)
        eth = generate_synthetic_ohlcv("ETH-USD", n_bars=50, seed=7)
        bench = _build_benchmark({"BTC-USD": btc, "ETH-USD": eth})

        self.assertIn("Open", bench.columns)
        common_dates = bench.index.intersection(btc.index)
        self.assertGreater(len(common_dates), 0)
        # The benchmark must be a genuinely different series from either
        # single leg -- otherwise excess_return degenerates to zero (see
        # _build_benchmark's docstring).
        self.assertFalse(bench["Open"].equals(btc["Open"]))
        self.assertFalse(bench["Open"].equals(eth["Open"]))


if __name__ == "__main__":
    unittest.main()
