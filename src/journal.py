"""
Step 5/6 of the workflow: log and review.

An append-only JSONL journal. Each decision is written ONCE, in full, before
any outcome is known. Outcomes are appended to the SAME row later (by
rewriting the file with the matching record's outcome fields filled in) but
the original decision-time fields are never modified — this is checked by
tests/test_journal.py.

Write safety: every read-modify-write cycle (append_decision, append_outcome)
runs inside an exclusive file lock (_locked, POSIX flock on a sidecar
`<path>.lock` file) so two overlapping invocations of this project's runners
(e.g. a manual run colliding with a scheduled one) can't race and silently
drop each other's rows. The write itself (_write_all) goes to a temp file in
the same directory and is atomically renamed into place (os.replace), so a
process killed mid-write leaves the previous, complete journal untouched
rather than a truncated/corrupt last line.
"""

from __future__ import annotations

import contextlib
import fcntl
import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from typing import Iterator, Optional


DECISION_FIELDS_LOCKED = (
    "record_id",
    "run_timestamp",
    "ticker",
    "signal_date",
    "thesis_direction",
    "thesis_confidence",
    "thesis_reasoning",
    "thesis_source",
    "risk_approved",
    "risk_size_fraction",
    "risk_reason",
    "action",
    "entry_date",
    "entry_price",
    "data_source",
)


@dataclass
class JournalRecord:
    record_id: str
    run_timestamp: str
    ticker: str
    signal_date: str
    thesis_direction: str
    thesis_confidence: float
    thesis_reasoning: str
    thesis_source: str
    risk_approved: bool
    risk_size_fraction: float
    risk_reason: str
    action: str  # "BUY" or "HOLD"
    entry_date: Optional[str]
    entry_price: Optional[float]
    data_source: str
    # Outcome fields — None until review() appends them.
    outcome_status: str = "PENDING"  # PENDING | COMPLETE
    exit_date: Optional[str] = None
    exit_price: Optional[float] = None
    stock_return: Optional[float] = None
    benchmark_return: Optional[float] = None
    excess_return: Optional[float] = None
    net_of_cost_return: Optional[float] = None


@contextlib.contextmanager
def _locked(path: str) -> Iterator[None]:
    """
    Hold an exclusive POSIX advisory lock (flock) for the duration of one
    read-modify-write cycle against `path`. Locks a sidecar `<path>.lock`
    file rather than `path` itself, since `path` gets replaced wholesale by
    _write_all's os.replace() and flock is tied to the underlying inode --
    locking the target file directly would stop protecting anything the
    instant a writer replaced it out from under the lock.
    """
    lock_dir = os.path.dirname(path) or "."
    os.makedirs(lock_dir, exist_ok=True)
    lock_path = path + ".lock"
    with open(lock_path, "w") as lock_f:
        fcntl.flock(lock_f, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_f, fcntl.LOCK_UN)


def _read_all(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _write_all(path: str, rows: list[dict]) -> None:
    """
    Write `rows` to `path` atomically: serialize to a temp file in the same
    directory, fsync it, then os.replace() it into place. A reader (or a
    process crash) never observes a partially-written file -- it sees either
    the complete previous version or the complete new version, never
    something in between.
    """
    dir_ = os.path.dirname(path) or "."
    os.makedirs(dir_, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=dir_, prefix=".journal_tmp_", suffix=".jsonl")
    try:
        with os.fdopen(fd, "w") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except BaseException:
        # Never leave a stray temp file behind on failure; the target path
        # is untouched either way since os.replace() never ran.
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def append_decision(path: str, record: JournalRecord) -> None:
    """Append a new decision record. Refuses to create a duplicate record_id."""
    with _locked(path):
        rows = _read_all(path)
        if any(r["record_id"] == record.record_id for r in rows):
            raise ValueError(f"Duplicate record_id, refusing to log again: {record.record_id}")
        rows.append(asdict(record))
        _write_all(path, rows)


def append_outcome(
    path: str,
    record_id: str,
    exit_date: str,
    exit_price: float,
    stock_return: float,
    benchmark_return: float,
    excess_return: float,
    net_of_cost_return: float,
) -> None:
    """
    Append a realized outcome to an existing record, WITHOUT modifying any
    of the locked decision-time fields. Raises if the record doesn't exist
    or is already complete (never overwrite a completed outcome).
    """
    with _locked(path):
        rows = _read_all(path)
        for row in rows:
            if row["record_id"] == record_id:
                if row["outcome_status"] == "COMPLETE":
                    raise ValueError(f"Record {record_id} already has a completed outcome; refusing to overwrite.")
                row["outcome_status"] = "COMPLETE"
                row["exit_date"] = exit_date
                row["exit_price"] = exit_price
                row["stock_return"] = stock_return
                row["benchmark_return"] = benchmark_return
                row["excess_return"] = excess_return
                row["net_of_cost_return"] = net_of_cost_return
                _write_all(path, rows)
                return
        raise ValueError(f"No record found with record_id={record_id}")


def load_journal(path: str) -> list[dict]:
    return _read_all(path)
