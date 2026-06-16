"""Tests for :mod:`arch_agent.services.recommendation`."""

from __future__ import annotations

import json
from pathlib import Path

from arch_agent.services.findings import Finding
from arch_agent.services.graph_loader import GraphLoader
from arch_agent.services.recommendation import build_report
from arch_agent.services.smells import SmellDetector

FIXTURE = Path(__file__).parent / "fixtures" / "graph.json"
TS = "2026-06-16T00:00:00+00:00"


def _fixture_findings() -> list[Finding]:
    return SmellDetector().detect(GraphLoader().load(FIXTURE))


def test_build_report_carries_findings_and_metadata() -> None:
    report = build_report(_fixture_findings(), repo="soarsmu/BugsInPy", generated_at=TS)
    assert report.repo == "soarsmu/BugsInPy"
    assert report.generated_at == TS
    assert len(report.findings) == len(_fixture_findings())


def test_to_json_round_trips_with_evidence() -> None:
    report = build_report(_fixture_findings(), repo="r", generated_at=TS)
    data = json.loads(report.to_json())
    assert data["repo"] == "r"
    assert data["generated_at"] == TS
    god = next(f for f in data["findings"] if f["smell"] == "god_node")
    assert god["node"] == "mod.core"
    assert god["evidence"]["fan_in"] == 6
    cyclic = next(f for f in data["findings"] if f["smell"] == "cyclic_dependency")
    assert isinstance(cyclic["evidence"]["cycle"], list)  # list survives JSON


def test_to_markdown_is_ranked_table_with_rationale() -> None:
    md = build_report(_fixture_findings(), repo="MyRepo", generated_at=TS).to_markdown()
    assert "# Recommendation Report — MyRepo" in md
    assert "| # | Severity | Smell | Node | Evidence | Recommendation |" in md
    assert "| 1 |" in md
    assert "## Rationale" in md
    assert "mod.core" in md


def test_markdown_ranks_match_finding_order() -> None:
    findings = _fixture_findings()
    md = build_report(findings, repo="r", generated_at=TS).to_markdown()
    first_row = next(line for line in md.splitlines() if line.startswith("| 1 |"))
    assert findings[0].node in first_row  # rank 1 == first (highest-priority) finding


def test_empty_findings() -> None:
    report = build_report([], repo="r", generated_at=TS)
    assert json.loads(report.to_json())["findings"] == []
    assert "No architectural smells detected." in report.to_markdown()


def test_summary_included_when_present() -> None:
    report = build_report([], repo="r", generated_at=TS, summary="Overall healthy.")
    assert "Overall healthy." in report.to_markdown()
    assert json.loads(report.to_json())["summary"] == "Overall healthy."


def test_default_generated_at_is_iso_timestamp() -> None:
    report = build_report([], repo="r")
    assert "T" in report.generated_at  # ISO 8601
