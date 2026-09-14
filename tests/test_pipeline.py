"""
Validation tests for the Phase 1 pipeline.

Run with: python3 -m pytest tests/ -v   (or python3 -m unittest discover)
"""

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from src.data import generate_synthetic_ohlcv, validate_ohlcv
from src.journal import JournalRecord, append_decision, append_outcome, load_journal
from src.risk import risk_check
from src.thesis import Thesis, stub_form_thesis
from src.workflow import gather_data, run_review_step, run_signal_step


class TestDataValidation(unittest.TestCase):
    def test_synthetic_data_passes_validation(self):
        df = generate_synthetic_ohlcv("TEST-USD", n_bars=100, seed=1)
        problems = validate_ohlcv(df, "TEST-USD")
        self.assertEqual(problems, [])

    def test_validation_catches_bad_high(self):
        df = generate_synthetic_ohlcv("TEST-USD", n_bars=50, seed=2)
        df.loc[df.index[10], "High"] = df["Low"].iloc[10] - 1  # corrupt it
        problems = validate_ohlcv(df, "TEST-USD")
        self.assertTrue(any("High" in p for p in problems))

    def test_validation_catches_duplicate_dates(self):
        df = generate_synthetic_ohlcv("TEST-USD", n_bars=50, seed=3)
        dup = pd.concat([df, df.iloc[[0]]])
        problems = validate_ohlcv(dup, "TEST-USD")
        self.assertTrue(any("duplicate" in p for p in problems))


class TestNoLookahead(unittest.TestCase):
    def test_gather_data_excludes_future_bars(self):
        df = generate_synthetic_ohlcv("TEST-USD", n_bars=50, seed=4)
        cutoff = df.index[20]
        visible = gather_data(df, cutoff)
        self.assertTrue((visible.index <= cutoff).all())
        self.assertEqual(visible.index[-1], cutoff)
        self.assertLess(len(visible), len(df))


class TestRiskCheck(unittest.TestCase):
    def test_flat_thesis_never_approved(self):
        t = Thesis(direction="FLAT", confidence=0.99, reasoning="x", source="STUB")
        r = risk_check(t, position_size_fraction=0.1)
        self.assertFalse(r.approved)
        self.assertEqual(r.size_fraction, 0.0)

    def test_low_confidence_long_rejected(self):
        t = Thesis(direction="LONG", confidence=0.1, reasoning="x", source="STUB")
        r = risk_check(t, position_size_fraction=0.1, min_confidence=0.4)
        self.assertFalse(r.approved)

    def test_confident_long_approved_with_fixed_size(self):
        t = Thesis(direction="LONG", confidence=0.8, reasoning="x", source="STUB")
        r = risk_check(t, position_size_fraction=0.1, min_confidence=0.4)
        self.assertTrue(r.approved)
        self.assertEqual(r.size_fraction, 0.1)


class TestJournalImmutability(unittest.TestCase):
    def setUp(self):
        self.path = "output/_test_journal.jsonl"
        if os.path.exists(self.path):
            os.remove(self.path)

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    def _make_record(self, record_id="r1"):
        return JournalRecord(
            record_id=record_id,
            run_timestamp="2026-01-01T00:00:00",
            ticker="TEST-USD",
            signal_date="2026-01-01",
            thesis_direction="LONG",
            thesis_confidence=0.8,
            thesis_reasoning="test",
            thesis_source="STUB",
            risk_approved=True,
            risk_size_fraction=0.1,
            risk_reason="test",
            action="BUY",
            entry_date="2026-01-02",
            entry_price=100.0,
            data_source="SYNTHETIC",
        )

    def test_duplicate_record_id_rejected(self):
        append_decision(self.path, self._make_record("dup1"))
        with self.assertRaises(ValueError):
            append_decision(self.path, self._make_record("dup1"))

    def test_outcome_appends_without_touching_decision_fields(self):
        rec = self._make_record("r2")
        append_decision(self.path, rec)
        append_outcome(
            self.path,
            record_id="r2",
            exit_date="2026-01-10",
            exit_price=110.0,
            stock_return=0.10,
            benchmark_return=0.05,
            excess_return=0.05,
            net_of_cost_return=0.097,
        )
        rows = load_journal(self.path)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        # Decision-time fields untouched.
        self.assertEqual(row["entry_price"], 100.0)
        self.assertEqual(row["thesis_reasoning"], "test")
        # Outcome fields populated.
        self.assertEqual(row["outcome_status"], "COMPLETE")
        self.assertEqual(row["exit_price"], 110.0)

    def test_completed_outcome_cannot_be_overwritten(self):
        rec = self._make_record("r3")
        append_decision(self.path, rec)
        append_outcome(
            self.path, record_id="r3", exit_date="2026-01-10", exit_price=110.0,
            stock_return=0.1, benchmark_return=0.05, excess_return=0.05, net_of_cost_return=0.097,
        )
        with self.assertRaises(ValueError):
            append_outcome(
                self.path, record_id="r3", exit_date="2026-01-11", exit_price=999.0,
                stock_return=9.0, benchmark_return=0.0, excess_return=9.0, net_of_cost_return=9.0,
            )


class TestWorkflowOrdering(unittest.TestCase):
    def setUp(self):
        self.path = "output/_test_workflow_journal.jsonl"
        if os.path.exists(self.path):
            os.remove(self.path)

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    def test_signal_step_produces_hold_when_thesis_flat(self):
        def always_flat(ticker, bars):
            return Thesis(direction="FLAT", confidence=0.9, reasoning="forced flat", source="STUB")

        hist = generate_synthetic_ohlcv("TEST-USD", n_bars=30, seed=5)
        record = run_signal_step(
            ticker="TEST-USD",
            full_history=hist,
            as_of_date=hist.index[10],
            journal_path=self.path,
            position_size_fraction=0.1,
            data_source="SYNTHETIC",
            thesis_fn=always_flat,
        )
        self.assertEqual(record.action, "HOLD")
        self.assertIsNone(record.entry_date)

    def test_signal_step_buy_has_next_bar_entry_not_same_bar(self):
        def always_long(ticker, bars):
            return Thesis(direction="LONG", confidence=0.9, reasoning="forced long", source="STUB")

        hist = generate_synthetic_ohlcv("TEST-USD", n_bars=30, seed=6)
        as_of = hist.index[10]
        record = run_signal_step(
            ticker="TEST-USD",
            full_history=hist,
            as_of_date=as_of,
            journal_path=self.path,
            position_size_fraction=0.1,
            data_source="SYNTHETIC",
            thesis_fn=always_long,
        )
        self.assertEqual(record.action, "BUY")
        self.assertIsNotNone(record.entry_date)
        # Entry date must be strictly after the signal date (next bar, not same bar).
        self.assertGreater(pd.Timestamp(record.entry_date), as_of)

    def test_review_step_uses_benchmark_same_dates(self):
        def always_long(ticker, bars):
            return Thesis(direction="LONG", confidence=0.9, reasoning="forced long", source="STUB")

        hist = generate_synthetic_ohlcv("TEST-USD", n_bars=30, seed=7)
        bench = generate_synthetic_ohlcv("BENCH", n_bars=30, seed=8)
        as_of = hist.index[5]
        record = run_signal_step(
            ticker="TEST-USD", full_history=hist, as_of_date=as_of,
            journal_path=self.path, position_size_fraction=0.1,
            data_source="SYNTHETIC", thesis_fn=always_long,
        )
        row = load_journal(self.path)[0]
        updated = run_review_step(
            record=row, full_history=hist, holding_period_bars=5,
            journal_path=self.path, taker_fee_bps=10, slippage_bps=5,
            benchmark_history=bench,
        )
        self.assertIsNotNone(updated)
        self.assertEqual(updated["outcome_status"], "COMPLETE")
        # net_of_cost_return should be lower than stock_return (costs applied)
        self.assertLess(updated["net_of_cost_return"], updated["stock_return"])


if __name__ == "__main__":
    unittest.main()
