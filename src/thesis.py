"""
Step 2 of the workflow: form_thesis.

This is the step the researcher explicitly chose to make a live LLM call
rather than a fixed rule. That decision is what makes Phase 2 (forward
paper trading) the only valid evidence-gathering phase — see
RESEARCH_SPEC.md for why a historical backtest of this step can't be
trusted.

This module defines the interface and a STUB implementation so Phase 1 can
exercise the full pipeline without any LLM access (this sandbox has no
credentials to call one). Before Phase 2, replace `stub_form_thesis` with a
real call to an LLM (via `form_thesis_fn` in workflow.py) that:
  - is given only data available as of the decision timestamp
  - returns a structured view + reasoning
  - is logged verbatim, before any outcome is known
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Direction = Literal["LONG", "FLAT"]


@dataclass(frozen=True)
class Thesis:
    direction: Direction
    confidence: float  # 0.0-1.0, self-reported
    reasoning: str
    source: str  # "STUB" in Phase 1; "LLM:<model-name>" once wired up


def stub_form_thesis(ticker: str, recent_bars) -> Thesis:
    """
    Deterministic, seeded, NON-LLM stand-in for the real thesis step.

    Uses only a simple momentum heuristic on the bars it's given (no lookahead
    — caller is responsible for only passing bars up to the decision date).
    This exists purely to let Phase 1 validate pipeline plumbing; it is not
    the hypothesis under test and its "reasoning" is templated, not real
    reasoning.
    """
    if len(recent_bars) < 2:
        return Thesis(
            direction="FLAT",
            confidence=0.0,
            reasoning="Insufficient history to form a view.",
            source="STUB",
        )

    ret = recent_bars["Close"].iloc[-1] / recent_bars["Close"].iloc[-5] - 1 \
        if len(recent_bars) >= 5 else recent_bars["Close"].iloc[-1] / recent_bars["Close"].iloc[0] - 1

    if ret > 0.01:
        direction: Direction = "LONG"
        confidence = min(0.9, 0.5 + abs(ret) * 5)
        reasoning = (
            f"[STUB, not a real LLM thesis] {ticker} closed up {ret:.2%} over the "
            "recent lookback window; templated momentum heuristic treats this as "
            "a tentative bullish signal."
        )
    else:
        direction = "FLAT"
        confidence = min(0.9, 0.5 + abs(ret) * 5)
        reasoning = (
            f"[STUB, not a real LLM thesis] {ticker} showed no meaningful recent "
            f"upward momentum ({ret:.2%} over the lookback window); templated "
            "heuristic stays flat."
        )

    return Thesis(direction=direction, confidence=confidence, reasoning=reasoning, source="STUB")
