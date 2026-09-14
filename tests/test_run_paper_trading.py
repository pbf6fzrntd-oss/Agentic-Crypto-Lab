"""
Integration-level tests for run_paper_trading.main() itself.

Every prior Phase 2 test (tests/test_phase2.py) covers individual helper
functions (_already_signaled, _build_benchmark, form_thesis_llm) in
isolation -- none of them exercised main()'s actual review-loop wiring,
which is exactly where the SYNTHETIC/REAL price-scale bug lived: main()
matched PENDING rows to review by (ticker, date-in-fetched-range) alone,
without checking what data each row's own decision was made on, so a
SYNTHETIC (Phase 1, ~$100-scale) entry got reviewed against a REAL
(~$77,000-scale) exit and produced a 760x "return" that was actually
appended to the committed journal.

This file is the regression test for that bug and for the idempotency
guarantee the project depends on to avoid double-billing the LLM. Like
test_phase2.py, everything here runs WITHOUT hitting any real network or
LLM API: fetch_ohlcv, validate_ohlcv, and form_thesis_llm are all patched
at the point run_paper_trading imports them, and CONFIG is swapped for a
temp-file-backed test config.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

import src.run_paper_trading as rpt
from src.config import Config
from src.data import generate_synthetic_ohlcv
from src.journal import JournalRecord, append_decision, load_journal
from src.thesis import Thesis


def _real_looking_history(ticker: str, n_bars: int = 40, start_price: float = 50_000.0) -> pd.DataFrame:
    """
    A price series shaped like real BTC/ETH-scale data (via the same
    seeded-random-walk generator Phase 1 uses for convenience), but
    relabeled REAL:yfinance -- standing in for what fetch_ohlcv() would
    actually return this run.
    """
    df = generate_synthetic_ohlcv(ticker, n_bars=n_bars, seed=42, start_price=start_price)
    df.attrs["data_source"] = "REAL:yfinance"
    df.attrs["ticker"] = ticker
    return df


class TestReviewPassNeverMixesDataSources(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.journal_path = str(Path(self.tmpdir.name) / "journal.jsonl")
        self.hist = _real_looking_history("BTC-USD", n_bars=40, start_price=50_000.0)

        self.test_config = Config(
            universe=("BTC-USD",),
            bar_interval="1d",
            lookback_days=40,
            holding_period_bars=5,
            position_size_fraction=0.1,
            taker_fee_bps=10.0,
            slippage_bps=5.0,
            data_dir=self.tmpdir.name,
            output_dir=self.tmpdir.name,
            journal_path=self.journal_path,
            dry_run_summary_path=str(Path(self.tmpdir.name) / "unused.csv"),
        )

        # A SYNTHETIC (Phase-1-scale) PENDING BUY, entered 10 bars in --
        # eligible for review (holding_period_bars=5 bars later is still
        # within the 40-bar history).
        entry_date = self.hist.index[10]
        self.synthetic_row = JournalRecord(
            record_id="synthetic-1",
            run_timestamp="2020-01-01T00:00:00+00:00",
            ticker="BTC-USD",
            signal_date=str((entry_date - pd.Timedelta(days=1)).date()),
            thesis_direction="LONG",
            thesis_confidence=0.9,
            thesis_reasoning="[STUB] phase 1 synthetic thesis",
            thesis_source="STUB",
            risk_approved=True,
            risk_size_fraction=0.1,
            risk_reason="test",
            action="BUY",
            entry_date=str(entry_date.date()),
            entry_price=100.0,  # Phase-1 synthetic price scale
            data_source="SYNTHETIC",
        )

        # A REAL PENDING BUY at the SAME ticker and entry_date, priced at
        # this history's own real scale -- the only row that should ever
        # get reviewed against self.hist.
        self.real_row = JournalRecord(
            record_id="real-1",
            run_timestamp="2026-09-01T00:00:00+00:00",
            ticker="BTC-USD",
            signal_date=str((entry_date - pd.Timedelta(days=1)).date()),
            thesis_direction="LONG",
            thesis_confidence=0.9,
            thesis_reasoning="a real thesis",
            thesis_source="LLM:claude-sonnet-5",
            risk_approved=True,
            risk_size_fraction=0.1,
            risk_reason="test",
            action="BUY",
            entry_date=str(entry_date.date()),
            entry_price=float(self.hist["Open"].loc[entry_date]),
            data_source="REAL:yfinance",
        )
        append_decision(self.journal_path, self.synthetic_row)
        append_decision(self.journal_path, self.real_row)

    def tearDown(self):
        self.tmpdir.cleanup()

    def _run_main(self, thesis_mock: MagicMock) -> None:
        with patch("src.run_paper_trading.CONFIG", self.test_config), \
             patch("src.run_paper_trading.fetch_ohlcv", return_value=self.hist), \
             patch("src.run_paper_trading.validate_ohlcv", return_value=[]), \
             patch("src.run_paper_trading.form_thesis_llm", thesis_mock):
            rpt.main()

    def test_synthetic_row_never_reviewed_against_real_prices(self):
        thesis_mock = MagicMock(return_value=Thesis(direction="FLAT", confidence=0.5, reasoning="x", source="LLM:x"))
        self._run_main(thesis_mock)

        rows = {r["record_id"]: r for r in load_journal(self.journal_path)}

        # The SYNTHETIC row must be completely untouched -- still PENDING,
        # no exit fields populated, no return computed.
        synthetic = rows["synthetic-1"]
        self.assertEqual(synthetic["outcome_status"], "PENDING")
        self.assertIsNone(synthetic["exit_price"])
        self.assertIsNone(synthetic["net_of_cost_return"])
        # And its decision-time fields (the ones that matter for the
        # immutability guarantee) are exactly as logged.
        self.assertEqual(synthetic["entry_price"], 100.0)

        # The REAL row, by contrast, IS eligible and must have been
        # reviewed, with a plausible (not corrupted) return.
        real = rows["real-1"]
        self.assertEqual(real["outcome_status"], "COMPLETE")
        self.assertIsNotNone(real["net_of_cost_return"])
        self.assertLess(abs(real["net_of_cost_return"]), 5.0)  # sane, not a scale-mismatch blowup

    def test_no_new_synthetic_style_completion_appears_in_journal(self):
        # Belt-and-suspenders on the same property: scan every COMPLETE row
        # after the run and confirm none of them is SYNTHETIC-sourced --
        # this is the exact shape the original bug produced (SYNTHETIC rows
        # flipping to COMPLETE with an absurd net_of_cost_return).
        thesis_mock = MagicMock(return_value=Thesis(direction="FLAT", confidence=0.5, reasoning="x", source="LLM:x"))
        self._run_main(thesis_mock)

        rows = load_journal(self.journal_path)
        completed_synthetic = [r for r in rows if r["data_source"] == "SYNTHETIC" and r["outcome_status"] == "COMPLETE"]
        self.assertEqual(completed_synthetic, [])


class TestIdempotency(unittest.TestCase):
    """
    A re-run (accidental double-invocation, or a retry after a partial
    failure) must never log a second decision -- and, more importantly,
    never make a second BILLED LLM call -- for a (ticker, signal_date) pair
    already in the journal.
    """

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.journal_path = str(Path(self.tmpdir.name) / "journal.jsonl")
        self.hist = _real_looking_history("BTC-USD", n_bars=40, start_price=50_000.0)
        self.test_config = Config(
            universe=("BTC-USD",),
            bar_interval="1d",
            lookback_days=40,
            holding_period_bars=5,
            position_size_fraction=0.1,
            taker_fee_bps=10.0,
            slippage_bps=5.0,
            data_dir=self.tmpdir.name,
            output_dir=self.tmpdir.name,
            journal_path=self.journal_path,
            dry_run_summary_path=str(Path(self.tmpdir.name) / "unused.csv"),
        )

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_second_run_makes_no_new_llm_calls_or_journal_rows(self):
        thesis_mock = MagicMock(return_value=Thesis(direction="FLAT", confidence=0.5, reasoning="x", source="LLM:x"))

        def run_once():
            with patch("src.run_paper_trading.CONFIG", self.test_config), \
                 patch("src.run_paper_trading.fetch_ohlcv", return_value=self.hist), \
                 patch("src.run_paper_trading.validate_ohlcv", return_value=[]), \
                 patch("src.run_paper_trading.form_thesis_llm", thesis_mock):
                rpt.main()

        run_once()
        rows_after_first = load_journal(self.journal_path)
        calls_after_first = thesis_mock.call_count
        self.assertEqual(calls_after_first, 1)  # one ticker, one new signal date

        run_once()
        rows_after_second = load_journal(self.journal_path)
        calls_after_second = thesis_mock.call_count

        self.assertEqual(calls_after_second, calls_after_first)  # no new billed call
        self.assertEqual(len(rows_after_second), len(rows_after_first))  # no new row


if __name__ == "__main__":
    unittest.main()
