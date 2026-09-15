"""
Tests for src/run_historical_validation.py.

Two things matter most here: it must NEVER touch the Anthropic API (no
form_thesis_llm, no cost), and its journal must stay completely separate
from both Phase 1's and Phase 2's. Tiny universe/lookback so this runs in
well under a second -- no network, no cost.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import src.run_historical_validation as rhv
from src.config import Config
from src.data import generate_synthetic_ohlcv
from src.journal import JournalRecord, append_decision, load_journal


class TestNeverCallsAnthropic(unittest.TestCase):
    def test_module_does_not_import_form_thesis_llm_or_cost_tracking(self):
        # Checks the actual import statements, not prose mentions -- the
        # module docstring/comments legitimately name form_thesis_llm and
        # ANTHROPIC_KEY_FOR_TRADING to explain what NOT to do. This catches
        # a future edit that reintroduces a real import of either, which
        # would defeat the entire point of this script.
        import ast

        source = Path(rhv.__file__).read_text()
        tree = ast.parse(source)
        imported_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imported_names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.Import):
                imported_names.update(alias.name for alias in node.names)

        self.assertNotIn("form_thesis_llm", imported_names)
        self.assertFalse(any(n.startswith("src.cost_tracking") or n == "cost_tracking" for n in imported_names))

    def test_main_never_touches_anthropic_even_if_installed(self):
        # Belt-and-suspenders: if anthropic.Anthropic were somehow called,
        # this patch would either no-op silently (if never invoked, as
        # expected) or the assert_not_called below would catch it.
        tmpdir = tempfile.TemporaryDirectory()
        try:
            hist = generate_synthetic_ohlcv("BTC-USD", n_bars=30, seed=1, start_price=50_000.0)
            hist.attrs["data_source"] = "REAL:yfinance"
            test_config = Config(
                universe=("BTC-USD",),
                historical_journal_path=str(Path(tmpdir.name) / "hist.jsonl"),
                historical_summary_path=str(Path(tmpdir.name) / "hist.csv"),
            )
            with patch("src.run_historical_validation.CONFIG", test_config), \
                 patch("src.run_historical_validation.fetch_ohlcv", return_value=hist), \
                 patch("src.run_historical_validation.validate_ohlcv", return_value=[]), \
                 patch("anthropic.Anthropic") as mock_anthropic:
                rhv.main()
            mock_anthropic.assert_not_called()
        finally:
            tmpdir.cleanup()


class TestJournalSeparation(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.hist_path = str(Path(self.tmpdir.name) / "historical.jsonl")
        self.real_journal_path = str(Path(self.tmpdir.name) / "real.jsonl")
        self.hist = generate_synthetic_ohlcv("BTC-USD", n_bars=30, seed=2, start_price=50_000.0)
        self.hist.attrs["data_source"] = "REAL:yfinance"
        self.test_config = Config(
            universe=("BTC-USD",),
            taker_fee_bps=10.0,
            slippage_bps=5.0,
            journal_path=self.real_journal_path,
            historical_journal_path=self.hist_path,
            historical_summary_path=str(Path(self.tmpdir.name) / "hist.csv"),
        )

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_never_touches_the_real_journal_path(self):
        append_decision(self.real_journal_path, JournalRecord(
            record_id="real-1", run_timestamp="2026-09-01T00:00:00+00:00",
            ticker="BTC-USD", signal_date="2026-09-01",
            thesis_direction="LONG", thesis_confidence=0.8,
            thesis_reasoning="real", thesis_source="LLM:claude-sonnet-5",
            risk_approved=True, risk_size_fraction=0.1, risk_reason="r",
            action="BUY", entry_date="2026-09-02", entry_price=50000.0,
            data_source="REAL:yfinance",
        ))

        with patch("src.run_historical_validation.CONFIG", self.test_config), \
             patch("src.run_historical_validation.fetch_ohlcv", return_value=self.hist), \
             patch("src.run_historical_validation.validate_ohlcv", return_value=[]):
            rhv.main()

        real_rows = load_journal(self.real_journal_path)
        self.assertEqual(len(real_rows), 1)
        self.assertEqual(real_rows[0]["record_id"], "real-1")  # untouched

        hist_rows = load_journal(self.hist_path)
        self.assertGreater(len(hist_rows), 0)

    def test_all_rows_use_the_stub_thesis_not_llm(self):
        with patch("src.run_historical_validation.CONFIG", self.test_config), \
             patch("src.run_historical_validation.fetch_ohlcv", return_value=self.hist), \
             patch("src.run_historical_validation.validate_ohlcv", return_value=[]):
            rhv.main()

        rows = load_journal(self.hist_path)
        self.assertGreater(len(rows), 0)
        self.assertTrue(all(r["thesis_source"] == "STUB" for r in rows))

    def test_rerun_regenerates_without_duplicate_error(self):
        with patch("src.run_historical_validation.CONFIG", self.test_config), \
             patch("src.run_historical_validation.fetch_ohlcv", return_value=self.hist), \
             patch("src.run_historical_validation.validate_ohlcv", return_value=[]):
            rhv.main()
            first = load_journal(self.hist_path)
            rhv.main()  # must not raise just because the file already exists
            second = load_journal(self.hist_path)

        self.assertEqual(len(first), len(second))


if __name__ == "__main__":
    unittest.main()
