"""
Daily report: what Phase 2's REAL paper-trading decisions actually show so
far.

This is a reporting tool only -- it reads output/decision_journal.jsonl
(Config.journal_path) and never writes to it, never touches
phase1_dry_run_journal.jsonl (Phase 1's SYNTHETIC data is explicitly
excluded from every number here), and never makes an API call. It answers
one question: if you stopped the research today, what would the Phase 2
evidence actually say?

Run with: python3 -m src.generate_report
Writes: Config.report_path (also prints the same report to stdout)

The report computation (compute_report_data) is a pure function over
already-loaded rows, kept separate from rendering/I/O specifically so it's
directly unit-testable without a real journal file -- see
tests/test_generate_report.py.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import CONFIG
from src.journal import load_journal

# RESEARCH_SPEC.md is explicit: "The falsification bar... can only be
# checked once enough completed outcomes exist to say anything
# statistically meaningful -- a handful of trades is not that bar." 30 is
# a conventional minimum-sample-size rule of thumb, not a number the
# researcher specifically chose -- it exists so the report itself doesn't
# silently start reading a small, noisy sample as a real result the moment
# a handful of trades complete.
MIN_OUTCOMES_FOR_A_READ = 30


def _mean(values: list) -> float | None:
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def _pct(x: float | None) -> str:
    return f"{x:+.2%}" if x is not None else "n/a"


def compute_report_data(rows: list[dict]) -> dict:
    """
    Pure function: everything the report needs, computed from already-
    loaded journal rows. SYNTHETIC (Phase 1) rows are excluded entirely --
    this report is about REAL evidence only, per RESEARCH_SPEC.md.
    """
    real_rows = [r for r in rows if r.get("data_source", "").startswith("REAL")]
    completed = [r for r in real_rows if r["outcome_status"] == "COMPLETE"]
    pending = [r for r in real_rows if r["outcome_status"] == "PENDING"]
    open_buys = [r for r in pending if r["action"] == "BUY"]

    by_action: dict[str, int] = {}
    for r in real_rows:
        by_action[r["action"]] = by_action.get(r["action"], 0) + 1

    per_ticker_rows: dict[str, list[dict]] = {}
    for r in completed:
        per_ticker_rows.setdefault(r["ticker"], []).append(r)

    def _win_rate(trs: list[dict]) -> float | None:
        return _mean([1.0 if r["net_of_cost_return"] > 0 else 0.0 for r in trs])

    overall = {
        "win_rate": _win_rate(completed),
        "mean_stock_return": _mean([r["stock_return"] for r in completed]),
        "mean_benchmark_return": _mean([r["benchmark_return"] for r in completed]),
        "mean_excess_return": _mean([r["excess_return"] for r in completed]),
        "mean_net_of_cost_return": _mean([r["net_of_cost_return"] for r in completed]),
    }

    per_ticker = {
        ticker: {
            "n": len(trs),
            "win_rate": _win_rate(trs),
            "mean_net_of_cost_return": _mean([r["net_of_cost_return"] for r in trs]),
        }
        for ticker, trs in sorted(per_ticker_rows.items())
    }

    return {
        "total_real_decisions": len(real_rows),
        "by_action": by_action,
        "n_completed": len(completed),
        "n_pending": len(pending),
        "n_open_buys": len(open_buys),
        "open_gross_exposure": sum(r["risk_size_fraction"] for r in open_buys),
        "overall": overall,
        "per_ticker": per_ticker,
        "has_enough_for_a_read": len(completed) >= MIN_OUTCOMES_FOR_A_READ,
    }


def render_markdown(data: dict, generated_at: str) -> str:
    lines = [
        f"# Phase 2 Daily Report — {generated_at}",
        "",
        "**This is a research status report, not investment advice.** Phase 2 is "
        "paper trading only — no real orders are ever placed. See `RESEARCH_SPEC.md` "
        "for the full methodology and the falsification bar this project is bound by.",
        "",
        "## Headline",
        "",
        f"- Real decisions logged: **{data['total_real_decisions']}**"
        + (f" ({', '.join(f'{k}: {v}' for k, v in sorted(data['by_action'].items()))})" if data["by_action"] else ""),
        f"- Completed outcomes: **{data['n_completed']}**  |  Still pending: **{data['n_pending']}**",
        f"- Currently open positions: **{data['n_open_buys']}** "
        f"({data['open_gross_exposure']:.1%} of notional)",
        "",
    ]

    if not data["has_enough_for_a_read"]:
        lines += [
            "## Reading this report",
            "",
            f"**Only {data['n_completed']} real outcome(s) have completed "
            f"(threshold for a read: {MIN_OUTCOMES_FOR_A_READ}).** RESEARCH_SPEC.md is "
            "explicit that a handful of trades is not enough to say anything statistically "
            "meaningful about the workflow's real quality. The numbers below are shown for "
            "transparency and to track the pipeline is running correctly — not as a signal "
            "of edge or no edge either way. Zero or few completed outcomes this early is "
            "the expected, correct state, not a problem.",
            "",
        ]
    else:
        lines += [
            "## Falsification check",
            "",
            "RESEARCH_SPEC.md's stated bar: *if any apparent edge over buy-and-hold "
            "disappears once realistic volatility, fees, and slippage are applied, the "
            "workflow does not have a validated edge.* Mean net-of-cost return below is "
            "the number that check hinges on.",
            "",
        ]

    o = data["overall"]
    if data["n_completed"] > 0:
        lines += [
            "## Overall performance (completed trades only)",
            "",
            "| Metric | Value |",
            "|---|---|",
            f"| Win rate (net-of-cost return > 0) | {_pct(o['win_rate'])} |",
            f"| Mean stock return | {_pct(o['mean_stock_return'])} |",
            f"| Mean benchmark return | {_pct(o['mean_benchmark_return'])} |",
            f"| Mean excess return (vs. benchmark) | {_pct(o['mean_excess_return'])} |",
            f"| Mean net-of-cost return | {_pct(o['mean_net_of_cost_return'])} |",
            "",
        ]
        if data["per_ticker"]:
            lines += [
                "## Per-ticker (completed trades only)",
                "",
                "| Ticker | N | Win rate | Mean net-of-cost return |",
                "|---|---|---|---|",
            ]
            for ticker, s in data["per_ticker"].items():
                lines.append(f"| {ticker} | {s['n']} | {_pct(s['win_rate'])} | {_pct(s['mean_net_of_cost_return'])} |")
            lines.append("")
    else:
        lines += ["## Overall performance", "", "No completed outcomes yet.", ""]

    lines += [
        "---",
        "*Generated by `src/generate_report.py` from `output/decision_journal.jsonl` "
        "(`REAL:*` rows only — Phase 1's synthetic data is never included in this report).*",
    ]
    return "\n".join(lines)


def main() -> None:
    rows = load_journal(CONFIG.journal_path)
    data = compute_report_data(rows)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    report = render_markdown(data, generated_at)

    print(report)

    out_path = Path(CONFIG.report_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report)
    print(f"\n(report also written to {out_path})", file=sys.stderr)


if __name__ == "__main__":
    main()
