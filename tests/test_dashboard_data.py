"""
Tests for src/dashboard_data.py -- the extra data (open positions, recent
decisions) the published dashboard artifact needs on top of
generate_report.py's own report numbers. No journal file, no network.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.dashboard_data import compute_dashboard_data


def _row(ticker="BTC-USD", action="HOLD", outcome_status="PENDING", run_timestamp="2026-09-15T00:00:00+00:00", **overrides):
    row = {
        "record_id": f"{ticker}-{run_timestamp}",
        "ticker": ticker,
        "signal_date": "2026-09-15 00:00:00",
        "run_timestamp": run_timestamp,
        "action": action,
        "thesis_direction": "LONG" if action == "BUY" else "FLAT",
        "thesis_confidence": 0.5,
        "risk_approved": action == "BUY",
        "risk_reason": "r",
        "entry_date": "2026-09-15 01:00:00" if action == "BUY" else None,
        "entry_price": 100.0 if action == "BUY" else None,
        "risk_size_fraction": 0.1 if action == "BUY" else 0.0,
        "data_source": "REAL:yfinance",
        "outcome_status": outcome_status,
        "stock_return": 0.05 if outcome_status == "COMPLETE" else None,
        "benchmark_return": 0.01 if outcome_status == "COMPLETE" else None,
        "excess_return": 0.04 if outcome_status == "COMPLETE" else None,
        "net_of_cost_return": 0.04 if outcome_status == "COMPLETE" else None,
    }
    row.update(overrides)
    return row


class TestComputeDashboardData(unittest.TestCase):
    def test_open_positions_only_includes_pending_buys(self):
        rows = [
            _row(ticker="BTC-USD", action="BUY", outcome_status="PENDING"),
            _row(ticker="ETH-USD", action="BUY", outcome_status="COMPLETE"),
            _row(ticker="XRP-USD", action="HOLD", outcome_status="PENDING"),
        ]
        data = compute_dashboard_data(rows)
        tickers = {p["ticker"] for p in data["open_positions"]}
        self.assertEqual(tickers, {"BTC-USD"})

    def test_recent_decisions_limited_and_ordered_by_run_timestamp(self):
        rows = [
            _row(ticker=f"T{i}", run_timestamp=f"2026-09-15T{i:02d}:00:00+00:00")
            for i in range(20)
        ]
        data = compute_dashboard_data(rows)
        self.assertEqual(len(data["recent_decisions"]), 12)
        self.assertEqual(data["recent_decisions"][-1]["ticker"], "T19")  # most recent last

    def test_blocked_position_note_surfaces_the_risk_reason(self):
        rows = [_row(ticker="XLM-USD", action="HOLD", risk_approved=False,
                      thesis_direction="LONG", risk_reason="Adding 10% would exceed the cap")]
        data = compute_dashboard_data(rows)
        self.assertEqual(data["recent_decisions"][0]["note"], "Adding 10% would exceed the cap")

    def test_flat_hold_has_no_note_even_though_not_approved(self):
        rows = [_row(ticker="ATOM-USD", action="HOLD", risk_approved=False,
                      thesis_direction="FLAT", risk_reason="Thesis direction is FLAT.")]
        data = compute_dashboard_data(rows)
        self.assertEqual(data["recent_decisions"][0]["note"], "")

    def test_synthetic_rows_excluded_from_both_lists(self):
        rows = [_row(ticker="FAKE-USD", action="BUY", data_source="SYNTHETIC")]
        data = compute_dashboard_data(rows)
        self.assertEqual(data["open_positions"], [])
        self.assertEqual(data["recent_decisions"], [])

    def test_report_key_matches_generate_report_output(self):
        rows = [_row()]
        data = compute_dashboard_data(rows)
        self.assertIn("total_real_decisions", data["report"])
        self.assertIn("has_enough_for_a_read", data["report"])


if __name__ == "__main__":
    unittest.main()
