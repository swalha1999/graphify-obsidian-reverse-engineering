"""Build a ranked, evidence-backed RecommendationReport (PLAN.md §3.2, PRD FR-9).

Turns the (already ranked) :class:`Finding` list from the ``SmellDetector`` into a
report that serialises to **JSON** and renders to **Markdown**. Pure and
deterministic — ``generated_at`` is injectable so output is reproducible.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from arch_agent.services.findings import Finding


@dataclass(frozen=True)
class RecommendationReport:
    """A ranked set of evidence-backed findings for one repo."""

    repo: str
    generated_at: str
    findings: tuple[Finding, ...]
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        """A JSON-serialisable view of the report."""
        return {
            "repo": self.repo,
            "generated_at": self.generated_at,
            "summary": self.summary,
            "findings": [asdict(f) for f in self.findings],
        }

    def to_json(self, *, indent: int = 2) -> str:
        """Serialise the report to JSON."""
        return json.dumps(self.to_dict(), indent=indent)

    def to_markdown(self) -> str:
        """Render the report as a ranked Markdown table + rationale."""
        head = [
            f"# Recommendation Report — {self.repo}",
            "",
            f"_Generated: {self.generated_at}_",
            "",
        ]
        if self.summary:
            head += [self.summary, ""]
        if not self.findings:
            return "\n".join([*head, "No architectural smells detected."])
        rows = [
            "| # | Severity | Smell | Node | Evidence | Recommendation |",
            "|---|---|---|---|---|---|",
        ]
        rationale = ["", "## Rationale"]
        for rank, finding in enumerate(self.findings, start=1):
            evidence = ", ".join(f"{k}={v}" for k, v in finding.evidence.items())
            rows.append(
                f"| {rank} | {finding.severity} | {finding.smell} | {finding.node} "
                f"| {evidence} | {finding.recommendation} |"
            )
            rationale.append(f"{rank}. **{finding.node}** — {finding.rationale}")
        return "\n".join([*head, *rows, *rationale])


def build_report(
    findings: list[Finding],
    repo: str,
    *,
    generated_at: str | None = None,
    summary: str = "",
) -> RecommendationReport:
    """Assemble a :class:`RecommendationReport` from ranked findings."""
    timestamp = generated_at or datetime.now(tz=UTC).isoformat()
    return RecommendationReport(
        repo=repo, generated_at=timestamp, findings=tuple(findings), summary=summary
    )
