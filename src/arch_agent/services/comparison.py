"""Baseline vs graph-guided comparison report (PRD FR-14, PRD_token_efficiency.md §5-§6).

Combines the two :class:`RunRecord`s into a JSON record and a Markdown table that
covers every measured dimension (tokens, files/units, iterations, root-cause speed)
plus the **token savings %**. Honest reporting (assignment §6.2): the figure is
shown as measured, and a small or negative result is reported as-is, not hidden.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from arch_agent.services.efficiency import RunRecord

_KPI_TARGET_PCT = 40.0


def _ttrc(record: RunRecord) -> str:
    if record.time_to_root_cause_s is None:
        return "n/a"
    return f"{record.time_to_root_cause_s:g}"


@dataclass(frozen=True)
class EfficiencyComparison:
    """Baseline vs graph-guided run, with the savings figure."""

    task: str
    baseline: RunRecord
    graph_guided: RunRecord

    def savings_pct(self) -> float:
        """Token reduction of graph-guided vs baseline (total in+out tokens)."""
        base = self.baseline.in_tokens + self.baseline.out_tokens
        guided = self.graph_guided.in_tokens + self.graph_guided.out_tokens
        if base == 0:
            return 0.0
        return round((base - guided) / base * 100, 1)

    def verdict(self) -> str:
        """A plain-English read of the savings against the KPI target."""
        pct = self.savings_pct()
        if pct >= _KPI_TARGET_PCT:
            return f"meets the >={_KPI_TARGET_PCT:.0f}% target"
        if pct > 0:
            return f"positive but below the {_KPI_TARGET_PCT:.0f}% target"
        return "no token savings (graph-guided used at least as many tokens)"

    def to_dict(self) -> dict[str, Any]:
        """JSON-serialisable comparison record (PLAN.md §3.3)."""
        return {
            "task": self.task,
            "baseline": self.baseline.to_dict(),
            "graph_guided": self.graph_guided.to_dict(),
            "savings_pct": self.savings_pct(),
        }

    def to_markdown(self) -> str:
        """Render the side-by-side comparison table + honest savings note."""
        b, g = self.baseline, self.graph_guided
        rows: list[tuple[str, object, object]] = [
            ("Input tokens", b.in_tokens, g.in_tokens),
            ("Output tokens", b.out_tokens, g.out_tokens),
            ("Total tokens", b.in_tokens + b.out_tokens, g.in_tokens + g.out_tokens),
            ("USD", f"{b.usd:.4f}", f"{g.usd:.4f}"),
            ("Files read", b.files_read, g.files_read),
            ("Units read", b.units_read, g.units_read),
            ("Iterations", b.iterations, g.iterations),
            ("Time to root cause (s)", _ttrc(b), _ttrc(g)),
            ("Root cause found", b.root_cause_found, g.root_cause_found),
            ("Tests green", b.tests_green, g.tests_green),
        ]
        return "\n".join(
            [
                f"# Token-Efficiency Comparison — {self.task}",
                "",
                "| Metric | Baseline (raw code) | Graph-guided |",
                "|---|---|---|",
                *[f"| {name} | {bv} | {gv} |" for name, bv, gv in rows],
                "",
                f"**Token savings (graph-guided vs baseline): {self.savings_pct()}%** "
                f"— {self.verdict()}.",
                "",
                "> Reported honestly per the brief: the figure is the measured token reduction on "
                "the same task; a small or negative result is shown as-is and reflects the target "
                "repo size and any agent overhead.",
            ]
        )


def build_comparison(
    task: str, baseline: RunRecord, graph_guided: RunRecord
) -> EfficiencyComparison:
    """Assemble an :class:`EfficiencyComparison` from the two run records."""
    return EfficiencyComparison(task=task, baseline=baseline, graph_guided=graph_guided)
