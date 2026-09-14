"""
Step 3 of the workflow: risk_check.

Fixed, mechanical position-sizing rule. Not optimized, not tuned against
results. Applied identically regardless of what the thesis step said, except
that a FLAT thesis always sizes to zero.
"""

from __future__ import annotations

from dataclasses import dataclass

from .thesis import Thesis


@dataclass(frozen=True)
class RiskDecision:
    approved: bool
    size_fraction: float  # fraction of notional portfolio
    reason: str


def risk_check(thesis: Thesis, position_size_fraction: float, min_confidence: float = 0.4) -> RiskDecision:
    if thesis.direction == "FLAT":
        return RiskDecision(approved=False, size_fraction=0.0, reason="Thesis direction is FLAT.")

    if thesis.confidence < min_confidence:
        return RiskDecision(
            approved=False,
            size_fraction=0.0,
            reason=f"Thesis confidence {thesis.confidence:.2f} below minimum {min_confidence:.2f}.",
        )

    return RiskDecision(
        approved=True,
        size_fraction=position_size_fraction,
        reason="Thesis directional with sufficient confidence; fixed sizing rule applied.",
    )
