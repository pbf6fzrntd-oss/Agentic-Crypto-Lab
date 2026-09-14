"""
Unit tests for src/cost_tracking.py.

form_thesis_llm()'s use of this module (the pre-call circuit breaker and
post-call logging) is covered separately in tests/test_phase2.py's
TestFormThesisLlm -- this file tests cost_tracking.py's own functions in
isolation. No network, no cost.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.cost_tracking import (
    MODEL_PRICING_USD_PER_MTOK,
    cumulative_cost_today,
    estimate_cost_usd,
    log_llm_call,
)


def _usage(input_tokens=0, output_tokens=0, cache_creation_input_tokens=0, cache_read_input_tokens=0):
    u = MagicMock()
    u.input_tokens = input_tokens
    u.output_tokens = output_tokens
    u.cache_creation_input_tokens = cache_creation_input_tokens
    u.cache_read_input_tokens = cache_read_input_tokens
    return u


class TestEstimateCostUsd(unittest.TestCase):
    def test_input_and_output_tokens_priced_correctly(self):
        rates = MODEL_PRICING_USD_PER_MTOK["claude-sonnet-5"]
        usage = _usage(input_tokens=1_000_000, output_tokens=1_000_000)
        cost = estimate_cost_usd("claude-sonnet-5", usage)
        self.assertAlmostEqual(cost, rates["input"] + rates["output"])

    def test_cache_write_and_read_priced_correctly(self):
        rates = MODEL_PRICING_USD_PER_MTOK["claude-sonnet-5"]
        usage = _usage(cache_creation_input_tokens=1_000_000, cache_read_input_tokens=1_000_000)
        cost = estimate_cost_usd("claude-sonnet-5", usage)
        self.assertAlmostEqual(cost, rates["cache_write"] + rates["cache_read"])

    def test_zero_usage_is_zero_cost(self):
        self.assertEqual(estimate_cost_usd("claude-sonnet-5", _usage()), 0.0)

    def test_unknown_model_falls_back_rather_than_raising(self):
        usage = _usage(input_tokens=1_000_000)
        cost = estimate_cost_usd("some-future-model", usage)
        self.assertGreater(cost, 0.0)  # falls back to claude-sonnet-5's rate, doesn't crash

    def test_missing_usage_field_treated_as_zero(self):
        # A minimal object exposing only input_tokens (e.g. an older SDK
        # response) must not raise on the other three fields.
        usage = MagicMock(spec=["input_tokens"])
        usage.input_tokens = 500
        cost = estimate_cost_usd("claude-sonnet-5", usage)
        self.assertGreater(cost, 0.0)


class TestLogAndCumulative(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.path = str(Path(self.tmpdir.name) / "cost_log.jsonl")

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_cumulative_cost_zero_when_no_log_exists(self):
        self.assertEqual(cumulative_cost_today(self.path), 0.0)

    def test_log_llm_call_returns_and_persists_the_same_cost(self):
        cost = log_llm_call(self.path, "claude-sonnet-5", "BTC-USD", _usage(input_tokens=1_000_000))
        self.assertAlmostEqual(cost, MODEL_PRICING_USD_PER_MTOK["claude-sonnet-5"]["input"])
        self.assertAlmostEqual(cumulative_cost_today(self.path), cost)

    def test_multiple_calls_accumulate(self):
        log_llm_call(self.path, "claude-sonnet-5", "BTC-USD", _usage(input_tokens=1_000_000))
        log_llm_call(self.path, "claude-sonnet-5", "ETH-USD", _usage(input_tokens=1_000_000))
        rates = MODEL_PRICING_USD_PER_MTOK["claude-sonnet-5"]
        self.assertAlmostEqual(cumulative_cost_today(self.path), 2 * rates["input"])

    def test_yesterdays_records_excluded_from_todays_total(self):
        # Write a record dated yesterday directly (log_llm_call always
        # stamps "now"), then confirm cumulative_cost_today ignores it.
        import json

        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        with open(self.path, "w") as f:
            f.write(json.dumps({
                "timestamp": yesterday, "ticker": "BTC-USD", "model": "claude-sonnet-5",
                "input_tokens": 1_000_000, "output_tokens": 0,
                "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0,
                "estimated_cost_usd": 2.00,
            }) + "\n")

        self.assertEqual(cumulative_cost_today(self.path), 0.0)

        log_llm_call(self.path, "claude-sonnet-5", "ETH-USD", _usage(input_tokens=1_000_000))
        rates = MODEL_PRICING_USD_PER_MTOK["claude-sonnet-5"]
        # Only today's new record counts, not yesterday's $2.00.
        self.assertAlmostEqual(cumulative_cost_today(self.path), rates["input"])


if __name__ == "__main__":
    unittest.main()
