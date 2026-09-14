"""
Step 5/6 of the workflow: log and review.

An append-only JSONL journal. Each decision is written ONCE, in full, before
any outcome is known. Outcomes are appended to the SAME row later (by
rewriting the file with the matching record's outcome fields filled in) but
the original decision-time fields are never modified — this is checked by
tests/test_journal.py.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from typing import Optional


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
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def append_decision(path: str, record: JournalRecord) -> None:
    """Append a new decision record. Refuses to create a duplicate record_id."""
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
