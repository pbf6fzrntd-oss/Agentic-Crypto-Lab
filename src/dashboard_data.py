"""
Emits the Phase 2 Ledger dashboard's data as one JSON blob on stdout: the
same report data generate_report.py computes, plus the open-positions and
recent-decisions lists the published dashboard artifact renders.

This exists so refreshing the published dashboard (a scheduled, unattended
task -- see the "Phase 2 daily report" Routine) is a mechanical
read-JSON/replace-three-constants/republish step rather than something
each fresh session has to reconstruct by hand from the raw journal.

Run with: python3 -m src.dashboard_data
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import CONFIG
from src.generate_report import compute_report_data
from src.journal import load_journal

RECENT_DECISIONS_LIMIT = 12


def compute_dashboard_data(rows: list[dict]) -> dict:
    report = compute_report_data(rows)
    real_rows = [r for r in rows if r.get("data_source", "").startswith("REAL")]

    open_positions = [
        {
            "ticker": r["ticker"],
            "signal_date": r["signal_date"],
            "entry_date": r["entry_date"],
            "entry_price": r["entry_price"],
            "size": r["risk_size_fraction"],
        }
        for r in sorted(real_rows, key=lambda r: r["run_timestamp"])
        if r["action"] == "BUY" and r["outcome_status"] == "PENDING"
    ]

    recent = sorted(real_rows, key=lambda r: r["run_timestamp"])[-RECENT_DECISIONS_LIMIT:]
    recent_decisions = [
        {
            "ticker": r["ticker"],
            "direction": r["thesis_direction"],
            "confidence": r["thesis_confidence"],
            "action": r["action"],
            "note": "" if r["risk_approved"] or r["thesis_direction"] == "FLAT" else r["risk_reason"],
        }
        for r in recent
    ]

    return {"report": report, "open_positions": open_positions, "recent_decisions": recent_decisions}


def main() -> None:
    rows = load_journal(CONFIG.journal_path)
    data = compute_dashboard_data(rows)
    data["report"]["generated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
