"""
Cost telemetry and a hard spending circuit-breaker for real LLM calls.

form_thesis_llm() (thesis.py) is this project's only billed API call. It
calls cumulative_cost_today() BEFORE every real call and refuses (raises)
rather than proceeding once Config.max_daily_cost_usd is reached -- a hard
stop, not just visibility -- then calls log_llm_call() after every
successful response to record what that call actually cost.

Pricing is Anthropic's published per-million-token rate for the model
actually used (see MODEL_PRICING_USD_PER_MTOK below, current as of
2026-09-14). This produces a best-effort ESTIMATE from response.usage, not
a substitute for the Anthropic Console's actual billed usage -- update the
table (and re-check the cache multipliers) if pricing ever changes; nothing
here re-derives it automatically.
"""

from __future__ import annotations

import contextlib
import fcntl
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Iterator

# USD per million tokens. cache_write is the default 5-minute ephemeral TTL
# rate (~1.25x the input rate); cache_read is ~0.1x the input rate -- both
# per Anthropic's documented prompt-caching multipliers.
MODEL_PRICING_USD_PER_MTOK = {
    "claude-sonnet-5": {
        "input": 2.00,
        "output": 10.00,
        "cache_write": 2.50,
        "cache_read": 0.20,
    },
}


@dataclass
class CostRecord:
    timestamp: str
    ticker: str
    model: str
    input_tokens: int
    output_tokens: int
    cache_creation_input_tokens: int
    cache_read_input_tokens: int
    estimated_cost_usd: float


def _usage_field(usage, name: str) -> int:
    """
    Read one token-count field off a response.usage object (or any object/
    mock exposing the same attributes). Anthropic's SDK always populates
    all four fields (0, not missing, when a call doesn't use caching), but
    this tolerates an older SDK or a test double that omits one.
    """
    val = getattr(usage, name, None)
    return val if val is not None else 0


def estimate_cost_usd(model: str, usage) -> float:
    """
    Best-effort USD estimate for one API call's response.usage. Falls back
    to claude-sonnet-5's rate for a model not in MODEL_PRICING_USD_PER_MTOK
    rather than raising -- an approximate number beats none for a cost
    guard, but this project only ever calls claude-sonnet-5 (see
    thesis.py's LLM_MODEL), so the fallback path is not expected to be hit
    in practice.
    """
    rates = MODEL_PRICING_USD_PER_MTOK.get(model, MODEL_PRICING_USD_PER_MTOK["claude-sonnet-5"])
    cost = (
        _usage_field(usage, "input_tokens") * rates["input"]
        + _usage_field(usage, "output_tokens") * rates["output"]
        + _usage_field(usage, "cache_creation_input_tokens") * rates["cache_write"]
        + _usage_field(usage, "cache_read_input_tokens") * rates["cache_read"]
    ) / 1_000_000
    return cost


@contextlib.contextmanager
def _locked(path: str) -> Iterator[None]:
    lock_dir = os.path.dirname(path) or "."
    os.makedirs(lock_dir, exist_ok=True)
    with open(path + ".lock", "w") as lock_f:
        fcntl.flock(lock_f, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_f, fcntl.LOCK_UN)


def log_llm_call(cost_log_path: str, model: str, ticker: str, usage) -> float:
    """
    Append one CostRecord for a completed, billed API call. This log is
    pure-append (never rewrites an existing line, unlike journal.py), so a
    true O(1) `open(path, "a")` under a lock is enough -- no need for
    journal.py's read-modify-write atomicity machinery. Returns this call's
    estimated cost in USD.
    """
    record = CostRecord(
        timestamp=datetime.now(timezone.utc).isoformat(),
        ticker=ticker,
        model=model,
        input_tokens=_usage_field(usage, "input_tokens"),
        output_tokens=_usage_field(usage, "output_tokens"),
        cache_creation_input_tokens=_usage_field(usage, "cache_creation_input_tokens"),
        cache_read_input_tokens=_usage_field(usage, "cache_read_input_tokens"),
        estimated_cost_usd=estimate_cost_usd(model, usage),
    )
    os.makedirs(os.path.dirname(cost_log_path) or ".", exist_ok=True)
    with _locked(cost_log_path):
        with open(cost_log_path, "a") as f:
            f.write(json.dumps(asdict(record)) + "\n")
    return record.estimated_cost_usd


def cumulative_cost_today(cost_log_path: str) -> float:
    """Sum of estimated_cost_usd for every record logged today (UTC calendar date)."""
    if not os.path.exists(cost_log_path):
        return 0.0
    today = datetime.now(timezone.utc).date().isoformat()
    total = 0.0
    with open(cost_log_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row["timestamp"].startswith(today):
                total += row["estimated_cost_usd"]
    return total
