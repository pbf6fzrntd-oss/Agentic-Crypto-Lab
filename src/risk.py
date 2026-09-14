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


def risk_check(
    thesis: Thesis,
    position_size_fraction: float,
    min_confidence: float = 0.4,
    current_gross_exposure: float = 0.0,
    max_gross_exposure_fraction: float = 1.0,
) -> RiskDecision:
    """
    `current_gross_exposure` / `max_gross_exposure_fraction` are a
    portfolio-level guard: the fraction of notional already committed to
    other approved positions THIS run, and the fixed cap that fraction must
    never exceed. Each ticker's risk_check is otherwise fully independent of
    every other ticker's -- with a small, fixed universe and a 10% per-name
    size, that was never enough to matter, but it stops being safe to ignore
    once the universe is wide enough that many names can signal LONG the
    same day (e.g. a shared market-wide rally). Both default so every
    existing call site (Phase 1's dry run, in particular) is unaffected:
    current_gross_exposure=0.0 forever means the cap never trips unless a
    caller actively accumulates and passes it across a loop, which only
    run_paper_trading.main() does.
    """
    if thesis.direction == "FLAT":
        return RiskDecision(approved=False, size_fraction=0.0, reason="Thesis direction is FLAT.")

    if thesis.confidence < min_confidence:
        return RiskDecision(
            approved=False,
            size_fraction=0.0,
            reason=f"Thesis confidence {thesis.confidence:.2f} below minimum {min_confidence:.2f}.",
        )

    prospective_exposure = current_gross_exposure + position_size_fraction
    if prospective_exposure > max_gross_exposure_fraction:
        return RiskDecision(
            approved=False,
            size_fraction=0.0,
            reason=(
                f"Adding {position_size_fraction:.2%} would bring this run's gross exposure to "
                f"{prospective_exposure:.2%}, over the {max_gross_exposure_fraction:.2%} portfolio "
                f"cap ({current_gross_exposure:.2%} already committed this run)."
            ),
        )

    return RiskDecision(
        approved=True,
        size_fraction=position_size_fraction,
        reason="Thesis directional with sufficient confidence; fixed sizing rule applied.",
    )
