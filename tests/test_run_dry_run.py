"""
Regression tests for run_dry_run.py's journal separation.

Phase 1 and Phase 2 used to share a single journal file, and Phase 1
unconditionally deletes and regenerates its journal on every run -- so
every Phase 1 re-run silently destroyed Phase 2's real evidence. Fixed by
giving Phase 1 its own Config.phase1_journal_path, entirely separate from
Config.journal_path (Phase 2's real-evidence file). See RESEARCH_SPEC.md's
"Journal separation" note.

Everything here uses a tiny synthetic universe/lookback so the full
pipeline runs in well under a second -- no network, no cost.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import src.run_dry_run as rdr
from src.config import Config
from src.journal import JournalRecord, append_decision, load_journal


class TestJournalSeparation(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.phase1_path = str(Path(self.tmpdir.name) / "phase1.jsonl")
        self.real_journal_path = str(Path(self.tmpdir.name) / "real.jsonl")
        self.test_config = Config(
            universe=("TEST-USD",),
            lookback_days=20,  # tiny, so this runs fast
            holding_period_bars=5,
            position_size_fraction=0.1,
            taker_fee_bps=10.0,
            slippage_bps=5.0,
            data_dir=self.tmpdir.name,
            output_dir=self.tmpdir.name,
            journal_path=self.real_journal_path,
            phase1_journal_path=self.phase1_path,
            dry_run_summary_path=str(Path(self.tmpdir.name) / "summary.csv"),
        )

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_normal_run_never_touches_the_real_journal_path(self):
        # Seed the REAL journal (a separate path) with a real-looking row,
        # exactly as Phase 2 would leave it. A Phase 1 run must not read,
        # write, or delete anything at that path.
        append_decision(
            self.real_journal_path,
            JournalRecord(
                record_id="real-1", run_timestamp="2026-09-01T00:00:00+00:00",
                ticker="BTC-USD", signal_date="2026-09-01",
                thesis_direction="LONG", thesis_confidence=0.8,
                thesis_reasoning="real", thesis_source="LLM:claude-sonnet-5",
                risk_approved=True, risk_size_fraction=0.1, risk_reason="r",
                action="BUY", entry_date="2026-09-02", entry_price=50000.0,
                data_source="REAL:yfinance",
            ),
        )

        with patch("src.run_dry_run.CONFIG", self.test_config):
            rdr.main()

        real_rows = load_journal(self.real_journal_path)
        self.assertEqual(len(real_rows), 1)
        self.assertEqual(real_rows[0]["record_id"], "real-1")
        self.assertEqual(real_rows[0]["entry_price"], 50000.0)  # untouched

        # And Phase 1's own journal DID get populated with SYNTHETIC rows.
        phase1_rows = load_journal(self.phase1_path)
        self.assertGreater(len(phase1_rows), 0)
        self.assertTrue(all(r["data_source"] == "SYNTHETIC" for r in phase1_rows))

    def test_rerun_regenerates_phase1_journal_without_error(self):
        with patch("src.run_dry_run.CONFIG", self.test_config):
            rdr.main()
            first_run_rows = load_journal(self.phase1_path)
            rdr.main()  # must not raise just because the file already exists
            second_run_rows = load_journal(self.phase1_path)

        self.assertEqual(len(first_run_rows), len(second_run_rows))

    def test_refuses_to_delete_a_phase1_journal_containing_real_rows(self):
        # Simulate CONFIG.phase1_journal_path having been misconfigured to
        # point at a file with real evidence in it (e.g. accidentally set
        # equal to journal_path). main() must refuse to delete it, not
        # silently wipe real rows on the very first line it runs.
        append_decision(
            self.phase1_path,
            JournalRecord(
                record_id="oops-real", run_timestamp="2026-09-01T00:00:00+00:00",
                ticker="BTC-USD", signal_date="2026-09-01",
                thesis_direction="LONG", thesis_confidence=0.8,
                thesis_reasoning="real", thesis_source="LLM:claude-sonnet-5",
                risk_approved=True, risk_size_fraction=0.1, risk_reason="r",
                action="BUY", entry_date="2026-09-02", entry_price=50000.0,
                data_source="REAL:yfinance",
            ),
        )

        with patch("src.run_dry_run.CONFIG", self.test_config):
            with self.assertRaises(RuntimeError) as ctx:
                rdr.main()
        self.assertIn("Refusing to delete", str(ctx.exception))

        # The misplaced real row must still be there, completely untouched.
        rows = load_journal(self.phase1_path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["record_id"], "oops-real")


if __name__ == "__main__":
    unittest.main()
