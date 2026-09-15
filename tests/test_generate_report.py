"""
Tests for src/generate_report.py.

compute_report_data() is a pure function over hand-built rows -- no journal
file, no network, no cost. render_markdown() is checked for the specific
framing RESEARCH_SPEC.md requires (don't read a small sample as a result).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.generate_report import MIN_OUTCOMES_FOR_A_READ, compute_report_data, render_markdown


def _real_row(ticker="BTC-USD", action="BUY", outcome_status="PENDING", **overrides):
    row = {
        "record_id": f"{ticker}-{outcome_status}-{overrides.get('signal_date', 'x')}",
        "ticker": ticker,
        "signal_date": "2026-09-15 00:00:00",
        "action": action,
        "data_source": "REAL:yfinance",
        "outcome_status": outcome_status,
        "risk_size_fraction": 0.1 if action == "BUY" else 0.0,
        "stock_return": None,
        "benchmark_return": None,
        "excess_return": None,
        "net_of_cost_return": None,
    }
    row.update(overrides)
    return row


def _synthetic_row(**overrides):
    row = _real_row(**overrides)
    row["data_source"] = "SYNTHETIC"
    return row


class TestComputeReportData(unittest.TestCase):
    def test_synthetic_rows_are_excluded_entirely(self):
        rows = [
            _real_row(action="HOLD", outcome_status="PENDING"),
            _synthetic_row(ticker="ETH-USD", action="BUY", outcome_status="COMPLETE", net_of_cost_return=99.0),
        ]
        data = compute_report_data(rows)
        self.assertEqual(data["total_real_decisions"], 1)
        self.assertEqual(data["n_completed"], 0)  # the SYNTHETIC completion must not count

    def test_counts_by_action_and_status(self):
        rows = [
            _real_row(ticker="BTC-USD", action="HOLD", outcome_status="PENDING"),
            _real_row(ticker="ETH-USD", action="BUY", outcome_status="PENDING"),
            _real_row(ticker="XRP-USD", action="BUY", outcome_status="COMPLETE", net_of_cost_return=0.05,
                      stock_return=0.06, benchmark_return=0.01, excess_return=0.05),
        ]
        data = compute_report_data(rows)
        self.assertEqual(data["total_real_decisions"], 3)
        self.assertEqual(data["by_action"], {"HOLD": 1, "BUY": 2})
        self.assertEqual(data["n_completed"], 1)
        self.assertEqual(data["n_pending"], 2)
        self.assertEqual(data["n_open_buys"], 1)  # the still-PENDING BUY, not the completed one
        self.assertAlmostEqual(data["open_gross_exposure"], 0.1)

    def test_win_rate_and_means_computed_correctly(self):
        rows = [
            _real_row(ticker="A", action="BUY", outcome_status="COMPLETE", net_of_cost_return=0.10,
                      stock_return=0.12, benchmark_return=0.02, excess_return=0.10),
            _real_row(ticker="B", action="BUY", outcome_status="COMPLETE", net_of_cost_return=-0.04,
                      stock_return=-0.02, benchmark_return=0.02, excess_return=-0.04),
        ]
        data = compute_report_data(rows)
        o = data["overall"]
        self.assertAlmostEqual(o["win_rate"], 0.5)  # 1 of 2 positive
        self.assertAlmostEqual(o["mean_net_of_cost_return"], 0.03)
        self.assertAlmostEqual(o["mean_stock_return"], 0.05)

    def test_per_ticker_breakdown(self):
        rows = [
            _real_row(ticker="BTC-USD", action="BUY", outcome_status="COMPLETE", net_of_cost_return=0.05,
                      stock_return=0.05, benchmark_return=0.0, excess_return=0.05),
            _real_row(ticker="BTC-USD", action="BUY", outcome_status="COMPLETE", net_of_cost_return=-0.02,
                      stock_return=-0.02, benchmark_return=0.0, excess_return=-0.02),
            _real_row(ticker="ETH-USD", action="BUY", outcome_status="COMPLETE", net_of_cost_return=0.01,
                      stock_return=0.01, benchmark_return=0.0, excess_return=0.01),
        ]
        data = compute_report_data(rows)
        self.assertEqual(data["per_ticker"]["BTC-USD"]["n"], 2)
        self.assertEqual(data["per_ticker"]["ETH-USD"]["n"], 1)
        self.assertAlmostEqual(data["per_ticker"]["BTC-USD"]["win_rate"], 0.5)

    def test_empty_journal_produces_all_zeros_not_an_error(self):
        data = compute_report_data([])
        self.assertEqual(data["total_real_decisions"], 0)
        self.assertEqual(data["n_completed"], 0)
        self.assertIsNone(data["overall"]["win_rate"])
        self.assertFalse(data["has_enough_for_a_read"])

    def test_has_enough_for_a_read_threshold(self):
        below = [_real_row(ticker=f"T{i}", outcome_status="COMPLETE", net_of_cost_return=0.01)
                 for i in range(MIN_OUTCOMES_FOR_A_READ - 1)]
        at = [_real_row(ticker=f"T{i}", outcome_status="COMPLETE", net_of_cost_return=0.01)
              for i in range(MIN_OUTCOMES_FOR_A_READ)]
        self.assertFalse(compute_report_data(below)["has_enough_for_a_read"])
        self.assertTrue(compute_report_data(at)["has_enough_for_a_read"])


class TestRenderMarkdown(unittest.TestCase):
    def test_small_sample_shows_non_evidentiary_framing_not_a_verdict(self):
        rows = [_real_row(ticker="BTC-USD", outcome_status="COMPLETE", net_of_cost_return=0.5)]  # 1 trade
        data = compute_report_data(rows)
        report = render_markdown(data, "2026-09-15 00:00 UTC")
        self.assertIn("not enough to say anything statistically", report)
        self.assertNotIn("Falsification check", report)

    def test_large_sample_shows_falsification_framing(self):
        rows = [_real_row(ticker=f"T{i}", outcome_status="COMPLETE", net_of_cost_return=0.01,
                           stock_return=0.01, benchmark_return=0.0, excess_return=0.01)
                for i in range(MIN_OUTCOMES_FOR_A_READ)]
        data = compute_report_data(rows)
        report = render_markdown(data, "2026-09-15 00:00 UTC")
        self.assertIn("Falsification check", report)
        self.assertIn("Overall performance", report)

    def test_report_never_claims_investment_advice(self):
        report = render_markdown(compute_report_data([]), "2026-09-15 00:00 UTC")
        self.assertIn("not investment advice", report)
        self.assertIn("paper trading only", report)


if __name__ == "__main__":
    unittest.main()
