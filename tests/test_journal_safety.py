"""
Write-safety tests for journal.py: atomic writes and exclusive locking.

These are regression coverage for two hardening changes made after the
project started running Phase 2 for real: _write_all() used to write
directly to the target path (a crash mid-write left a truncated/corrupt
last line), and append_decision()/append_outcome() had no locking around
their read-modify-write cycle (two overlapping invocations could race and
silently drop a row). Neither failure mode was ever observed in production
here, but both are cheap to close and expensive to debug if they ever
happen against the real journal.

Everything here runs against temp files only -- no network, no cost.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import journal as journal_mod
from src.journal import JournalRecord, append_decision, append_decisions, append_outcomes, load_journal


def _record(record_id: str) -> JournalRecord:
    return JournalRecord(
        record_id=record_id,
        run_timestamp="2026-01-01T00:00:00+00:00",
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


class TestAtomicWrite(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmpdir.name, "journal.jsonl")

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_successful_write_is_readable_and_complete(self):
        append_decision(self.path, _record("r1"))
        append_decision(self.path, _record("r2"))
        rows = load_journal(self.path)
        self.assertEqual({r["record_id"] for r in rows}, {"r1", "r2"})

    def test_no_stray_temp_files_left_behind_after_writes(self):
        append_decision(self.path, _record("r1"))
        append_decision(self.path, _record("r2"))
        leftovers = [f for f in os.listdir(self.tmpdir.name) if f.startswith(".journal_tmp_")]
        self.assertEqual(leftovers, [])

    def test_failed_write_leaves_previous_journal_untouched(self):
        # First write succeeds normally.
        append_decision(self.path, _record("r1"))
        before = load_journal(self.path)

        # Force _write_all's serialization to blow up partway through (a
        # non-JSON-serializable value in one row simulates a crash mid-write)
        # and confirm the target file still holds the last GOOD version --
        # never a truncated one -- because the failure happens on the temp
        # file, before os.replace() ever runs.
        with patch("src.journal.json.dumps", side_effect=TypeError("boom")):
            with self.assertRaises(TypeError):
                append_decision(self.path, _record("r2"))

        after = load_journal(self.path)
        self.assertEqual(after, before)

        # And no half-written temp file left behind either.
        leftovers = [f for f in os.listdir(self.tmpdir.name) if f.startswith(".journal_tmp_")]
        self.assertEqual(leftovers, [])

    def test_write_uses_replace_not_in_place_truncation(self):
        # A file's inode changes across os.replace(); if _write_all ever
        # regresses to open(path, "w") + write in place, this would start
        # failing since the inode would stay constant across writes.
        append_decision(self.path, _record("r1"))
        inode_1 = os.stat(self.path).st_ino
        append_decision(self.path, _record("r2"))
        inode_2 = os.stat(self.path).st_ino
        self.assertNotEqual(inode_1, inode_2)


class TestLocking(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmpdir.name, "journal.jsonl")

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_concurrent_appends_all_land_with_no_lost_updates(self):
        # Without the lock, two threads' read-modify-write cycles for
        # append_decision could interleave: both read the same N rows,
        # both write back N+1 rows, and one of the two new records is lost.
        # With the lock, every one of these must land.
        n = 20
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = [pool.submit(append_decision, self.path, _record(f"r{i}")) for i in range(n)]
            for f in as_completed(futures):
                f.result()  # re-raise any exception from a worker

        rows = load_journal(self.path)
        self.assertEqual(len(rows), n)
        self.assertEqual({r["record_id"] for r in rows}, {f"r{i}" for i in range(n)})

    def test_lock_file_created_alongside_journal(self):
        append_decision(self.path, _record("r1"))
        self.assertTrue(os.path.exists(self.path + ".lock"))

    def test_journal_file_itself_is_valid_jsonl_after_concurrent_writes(self):
        n = 10
        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = [pool.submit(append_decision, self.path, _record(f"x{i}")) for i in range(n)]
            for f in as_completed(futures):
                f.result()

        with open(self.path) as f:
            lines = [line for line in f if line.strip()]
        self.assertEqual(len(lines), n)
        for line in lines:
            json.loads(line)  # each line must parse on its own -- no interleaved partial rows


class TestBulkAppend(unittest.TestCase):
    """
    append_decisions() / append_outcomes() -- batched writes added so Phase
    1's dry run (thousands of records in one invocation) isn't one
    lock+read+rewrite+fsync cycle PER record. Same correctness guarantees
    as the single-record functions, just checked/applied as one batch.
    """

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmpdir.name, "journal.jsonl")

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_batch_of_decisions_all_land_in_one_write(self):
        records = [_record(f"r{i}") for i in range(50)]
        append_decisions(self.path, records)
        rows = load_journal(self.path)
        self.assertEqual(len(rows), 50)
        self.assertEqual({r["record_id"] for r in rows}, {f"r{i}" for i in range(50)})

    def test_empty_batch_is_a_no_op(self):
        append_decisions(self.path, [])
        self.assertFalse(os.path.exists(self.path))

    def test_batch_with_internal_duplicate_writes_nothing(self):
        records = [_record("dup"), _record("dup")]
        with self.assertRaises(ValueError):
            append_decisions(self.path, records)
        self.assertFalse(os.path.exists(self.path))

    def test_batch_colliding_with_existing_row_writes_nothing_new(self):
        append_decision(self.path, _record("existing"))
        with self.assertRaises(ValueError):
            append_decisions(self.path, [_record("new1"), _record("existing")])
        # Neither "new1" nor a second "existing" was written -- all-or-nothing.
        rows = load_journal(self.path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["record_id"], "existing")

    def test_batch_of_outcomes_all_apply_in_one_write(self):
        records = [_record(f"o{i}") for i in range(20)]
        append_decisions(self.path, records)
        outcomes = [
            {
                "record_id": f"o{i}", "exit_date": "2026-01-10", "exit_price": 110.0 + i,
                "stock_return": 0.1, "benchmark_return": 0.05, "excess_return": 0.05,
                "net_of_cost_return": 0.097,
            }
            for i in range(20)
        ]
        append_outcomes(self.path, outcomes)
        rows = load_journal(self.path)
        self.assertTrue(all(r["outcome_status"] == "COMPLETE" for r in rows))
        self.assertEqual({r["exit_price"] for r in rows}, {110.0 + i for i in range(20)})

    def test_outcomes_batch_referencing_missing_record_writes_nothing(self):
        append_decisions(self.path, [_record("real1")])
        before = load_journal(self.path)
        with self.assertRaises(ValueError):
            append_outcomes(self.path, [
                {"record_id": "real1", "exit_date": "2026-01-10", "exit_price": 110.0,
                 "stock_return": 0.1, "benchmark_return": 0.05, "excess_return": 0.05, "net_of_cost_return": 0.097},
                {"record_id": "ghost", "exit_date": "2026-01-10", "exit_price": 1.0,
                 "stock_return": 0.0, "benchmark_return": 0.0, "excess_return": 0.0, "net_of_cost_return": 0.0},
            ])
        # "real1" must NOT have been partially updated -- validated before any write.
        after = load_journal(self.path)
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
