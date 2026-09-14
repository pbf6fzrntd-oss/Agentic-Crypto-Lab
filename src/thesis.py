"""
Step 2 of the workflow: form_thesis.

This is the step the researcher explicitly chose to make a live LLM call
rather than a fixed rule. That decision is what makes Phase 2 (forward
paper trading) the only valid evidence-gathering phase — see
RESEARCH_SPEC.md for why a historical backtest of this step can't be
trusted.

Phase 1 used `stub_form_thesis`, a deterministic, non-LLM momentum
heuristic, to exercise the full pipeline without any LLM access. Phase 2
adds `form_thesis_llm` below — a real call to Claude — which is the actual
subject of this project's research question.

Model and context size were asked of, and confirmed by, the researcher
before this was implemented (see RESEARCH_SPEC.md / the commit that added
this function): model `claude-sonnet-5`, context = last CONTEXT_BARS (60)
daily bars plus a few derived stats. Both are module-level constants below,
not CONFIG fields — CONFIG in config.py holds the *frozen* Phase 1
parameters (universe, sizing, costs, workflow order) that this project
commits not to tune against results; the thesis model/context choice is an
LLM-call setting, not one of those frozen research parameters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

Direction = Literal["LONG", "FLAT"]

# --- Phase 2 LLM thesis settings ---
LLM_MODEL = "claude-sonnet-5"
CONTEXT_BARS = 60  # bars of history shown to the model per call
MIN_BARS_FOR_LLM_THESIS = 10  # below this, there's not enough signal to ask

_SYSTEM_PROMPT = """\
You are the thesis-formation step in a mechanical research pipeline \
studying whether a structured agent decision workflow beats passive \
buy-and-hold on crypto, once volatility and costs are accounted for. This \
is Phase 2 of that study: forward paper trading. No real orders are ever \
placed anywhere in this system; this is a hypothetical, research-only \
exercise and nothing you say is investment advice.

You will be shown recent daily OHLCV price data for one crypto asset, \
ending at the most recent bar you may see. You have no visibility into \
anything after it, and none will ever be given to you before its date has \
passed. Form a short-term (about five trading days) directional view based \
ONLY on the data provided in this message.

Rules:
- Do not use any knowledge of this asset's actual historical or future \
price that you may recall from training. Reason only from the numbers \
given to you here — if your training data disagrees with these numbers, \
the numbers given here are what actually happened and what you must use.
- Your reasoning must be a few plain-language sentences explaining what in \
the given data drove your view. It will be logged verbatim as the research \
record for this decision, before any outcome is known.
- confidence is your own self-assessed probability (0.0-1.0) that the \
direction you name will be correct over the next ~5 trading days. Vary it \
honestly based on how strong or weak the signal looks to you — do not \
default to a fixed number.
- direction is LONG (bullish) or FLAT (no edge, bearish, or genuinely \
uncertain). There is no SHORT in this pipeline.

Call the record_thesis tool with your answer. Do not include any other \
text in your response.
"""

_THESIS_TOOL = {
    "name": "record_thesis",
    "description": "Record your directional thesis for this asset as of the given date.",
    "input_schema": {
        "type": "object",
        "properties": {
            "direction": {"type": "string", "enum": ["LONG", "FLAT"]},
            # NOTE: no "minimum"/"maximum" here -- Anthropic's strict tool-schema
            # mode rejects those keywords on a "number" type (400
            # invalid_request_error). The [0.0, 1.0] range is documented for the
            # model below and enforced at runtime instead, in form_thesis_llm.
            "confidence": {
                "type": "number",
                "description": "Self-assessed probability in [0.0, 1.0] that the named direction is correct.",
            },
            "reasoning": {"type": "string"},
        },
        "required": ["direction", "confidence", "reasoning"],
        "additionalProperties": False,
    },
    "strict": True,
}


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


def _derived_stats(window: pd.DataFrame) -> dict:
    """A few cheap-to-compute descriptive stats over the given window."""
    import numpy as np  # local import; only this helper needs numpy

    close = window["Close"]
    daily_log_returns = np.log(close / close.shift(1)).dropna()
    window_return = close.iloc[-1] / close.iloc[0] - 1
    realized_vol = daily_log_returns.std() if len(daily_log_returns) > 1 else float("nan")
    window_high = window["High"].max()
    window_low = window["Low"].min()
    last_close = close.iloc[-1]
    return {
        "window_return": window_return,
        "realized_daily_vol": realized_vol,
        "dist_from_high": last_close / window_high - 1,
        "dist_from_low": last_close / window_low - 1,
    }


def _build_user_message(ticker: str, window: pd.DataFrame) -> str:
    stats = _derived_stats(window)
    as_of_date = window.index[-1].date()

    lines = [
        f"Asset: {ticker}",
        f"Data through: {as_of_date} (most recent bar available; nothing after this date exists in this call)",
        f"Bars: last {len(window)} daily bars, oldest to newest",
        "",
        "Date,Open,High,Low,Close,Volume",
    ]
    for date, row in window.iterrows():
        lines.append(
            f"{date.date()},{row['Open']:.2f},{row['High']:.2f},"
            f"{row['Low']:.2f},{row['Close']:.2f},{row['Volume']:.0f}"
        )
    lines += [
        "",
        "Derived stats over this window:",
        f"- {len(window)}-bar return: {stats['window_return']:.2%}",
        f"- Realized daily volatility (stdev of daily log returns): {stats['realized_daily_vol']:.2%}",
        f"- Distance from window high: {stats['dist_from_high']:.2%}",
        f"- Distance from window low: {stats['dist_from_low']:.2%}",
    ]
    return "\n".join(lines)


def form_thesis_llm(ticker: str, recent_bars: pd.DataFrame) -> Thesis:
    """
    Real Phase 2 thesis step: a live call to Claude.

    `recent_bars` must already be no-lookahead-safe (the caller,
    `workflow.run_signal_step`, only ever passes bars up to and including
    the decision date via `gather_data()`). This function trims that
    further to the last CONTEXT_BARS bars before sending anything to the
    model — it never widens what it was given, only narrows it.

    Reads the API key from the ANTHROPIC_KEY_FOR_TRADING environment
    variable — this project's dedicated key for Phase 2 trading calls,
    kept separate from the SDK's default ANTHROPIC_API_KEY resolution so it
    can't collide with a key set for some other purpose in the same
    environment — never hardcode a key here. Raises on any failure (missing
    key, bad response shape, API error) rather than silently falling back
    to a fabricated thesis; the caller (the Phase 2 runner) is responsible
    for not logging a decision when this raises.

    Cost circuit breaker: refuses to make the call (raises, before ever
    touching the network) once today's cumulative estimated spend has
    reached Config.max_daily_cost_usd -- see src/cost_tracking.py. Every
    successful call is logged there afterward regardless of outcome.
    """
    import os

    import anthropic

    from .config import CONFIG
    from .cost_tracking import cumulative_cost_today, log_llm_call

    if len(recent_bars) < MIN_BARS_FOR_LLM_THESIS:
        # No API call needed (and none made) below this bar count, so don't
        # require a key just to hit this early, keyless return.
        return Thesis(
            direction="FLAT",
            confidence=0.0,
            reasoning=(
                f"Insufficient history ({len(recent_bars)} bars, need "
                f"{MIN_BARS_FOR_LLM_THESIS}) to ask for a thesis yet."
            ),
            source=f"LLM:{LLM_MODEL}",
        )

    api_key = os.environ.get("ANTHROPIC_KEY_FOR_TRADING")
    if not api_key:
        raise RuntimeError(
            "form_thesis_llm: ANTHROPIC_KEY_FOR_TRADING environment variable is not set"
        )

    spent_today = cumulative_cost_today(CONFIG.cost_log_path)
    if spent_today >= CONFIG.max_daily_cost_usd:
        raise RuntimeError(
            f"form_thesis_llm({ticker}): daily cost cap reached (${spent_today:.4f} spent >= "
            f"${CONFIG.max_daily_cost_usd:.2f} max_daily_cost_usd) -- refusing to make another "
            "billed Anthropic API call today. Raise Config.max_daily_cost_usd if this is expected."
        )

    window = recent_bars.tail(CONTEXT_BARS)
    user_message = _build_user_message(ticker, window)

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=LLM_MODEL,
        max_tokens=1024,
        # This is a short directional judgment call over ~60 price bars, not
        # a hard multi-step reasoning problem -- low effort keeps thinking
        # (on by default for claude-sonnet-5) bounded, which matters for
        # cost on a call this project makes routinely. Raise this if the
        # thesis quality looks shallow in practice.
        output_config={"effort": "low"},
        system=[{"type": "text", "text": _SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        tools=[_THESIS_TOOL],
        tool_choice={"type": "tool", "name": "record_thesis"},
        messages=[{"role": "user", "content": user_message}],
    )
    # Log the call (and what it cost) regardless of what happens below --
    # it was billed either way, and the circuit breaker above needs an
    # accurate running total even if this response turns out unparseable.
    log_llm_call(CONFIG.cost_log_path, LLM_MODEL, ticker, response.usage)

    tool_call = next((b for b in response.content if b.type == "tool_use"), None)
    if tool_call is None:
        raise RuntimeError(
            f"form_thesis_llm({ticker}): model response had no tool_use block "
            f"(stop_reason={response.stop_reason!r})"
        )

    data = tool_call.input  # already-parsed dict; strict:true guarantees the schema
    direction = data["direction"]
    if direction not in ("LONG", "FLAT"):
        raise RuntimeError(f"form_thesis_llm({ticker}): unexpected direction {direction!r}")

    # confidence's [0.0, 1.0] range can't be expressed in the strict tool
    # schema (see _THESIS_TOOL), so it's checked here instead.
    confidence = float(data["confidence"])
    if not (0.0 <= confidence <= 1.0):
        raise RuntimeError(f"form_thesis_llm({ticker}): confidence {confidence!r} out of [0.0, 1.0]")

    return Thesis(
        direction=direction,
        confidence=confidence,
        reasoning=str(data["reasoning"]),
        source=f"LLM:{LLM_MODEL}",
    )
