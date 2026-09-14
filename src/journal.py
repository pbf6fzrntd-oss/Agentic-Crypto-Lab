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


def append_decisions(path: str, records: list[JournalRecord]) -> None:
    """
    Append multiple new decision records in ONE locked read-modify-write
    cycle, instead of one append_decision() call per record.

    append_decision() is O(current file size) per call (full read + full
    rewrite + fsync), so calling it once per record in a tight loop is
    O(n^2) overall -- fine for Phase 2 (a handful of calls per day), but
    Phase 1's dry run logs thousands of records in a single invocation and
    that quadratic cost (compounded by the per-call fsync+flock this
    project added for write safety) made a full run take minutes instead
    of seconds. Callers with many records to log at once (run_dry_run.py)
    should collect them and call this once instead.

    Writes nothing if ANY record_id in the batch collides with an existing
    row or with another record in the same batch -- same all-or-nothing
    refusal as append_decision(), just checked for the whole batch upfront.
    """
    if not records:
        return
    new_ids = [r.record_id for r in records]
    seen: set[str] = set()
    dupes_in_batch = {i for i in new_ids if i in seen or seen.add(i)}  # type: ignore[func-returns-value]
    if dupes_in_batch:
        raise ValueError(f"Duplicate record_id(s) within batch, refusing to log any of it: {dupes_in_batch}")

    with _locked(path):
        rows = _read_all(path)
        existing_ids = {r["record_id"] for r in rows}
        collisions = existing_ids & set(new_ids)
        if collisions:
            raise ValueError(f"Duplicate record_id(s), refusing to log again: {collisions}")
        rows.extend(asdict(r) for r in records)
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


def append_outcomes(path: str, outcomes: list[dict]) -> None:
    """
    Append multiple realized outcomes in ONE locked read-modify-write
    cycle -- same batching rationale as append_decisions(), for the same
    reason (Phase 1's review pass can complete thousands of outcomes in a
    single run). Each entry in `outcomes` is a dict with keys: record_id,
    exit_date, exit_price, stock_return, benchmark_return, excess_return,
    net_of_cost_return (extra keys, e.g. the rest of a full journal row
    dict, are ignored).

    Validates every entry BEFORE writing any of them: raises (writing
    nothing) if any record_id is missing, already COMPLETE, or appears
    more than once in this batch -- same all-or-nothing guarantee as
    append_outcome() for a single record.
    """
    if not outcomes:
        return
    ids = [o["record_id"] for o in outcomes]
    if len(ids) != len(set(ids)):
        seen: set[str] = set()
        dupes = {i for i in ids if i in seen or seen.add(i)}  # type: ignore[func-returns-value]
        raise ValueError(f"Duplicate record_id(s) within outcomes batch, refusing to log any of it: {dupes}")

    with _locked(path):
        rows = _read_all(path)
        by_id = {r["record_id"]: r for r in rows}
        for o in outcomes:
            row = by_id.get(o["record_id"])
            if row is None:
                raise ValueError(f"No record found with record_id={o['record_id']}")
            if row["outcome_status"] == "COMPLETE":
                raise ValueError(f"Record {o['record_id']} already has a completed outcome; refusing to overwrite.")
        for o in outcomes:
            row = by_id[o["record_id"]]
            row["outcome_status"] = "COMPLETE"
            row["exit_date"] = o["exit_date"]
            row["exit_price"] = o["exit_price"]
            row["stock_return"] = o["stock_return"]
            row["benchmark_return"] = o["benchmark_return"]
            row["excess_return"] = o["excess_return"]
            row["net_of_cost_return"] = o["net_of_cost_return"]
        _write_all(path, rows)


def load_journal(path: str) -> list[dict]:
    return _read_all(path)
