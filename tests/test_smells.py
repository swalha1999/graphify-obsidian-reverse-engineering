"""Tests for :mod:`arch_agent.services.smells` and :mod:`arch_agent.services.findings`."""

from __future__ import annotations

from pathlib import Path

from arch_agent.services.findings import Finding, SmellConfig
from arch_agent.services.graph_loader import GraphLoader
from arch_agent.services.models import Edge, EdgeKind, GraphModel, Node, NodeType
from arch_agent.services.smells import SmellDetector

FIXTURE = Path(__file__).parent / "fixtures" / "graph.json"


def _fixture() -> GraphModel:
    return GraphLoader().load(FIXTURE)


def _by_smell(findings: list[Finding], smell: str) -> list[Finding]:
    return [f for f in findings if f.smell == smell]


def test_default_config_detects_three_smells_on_fixture() -> None:
    findings = SmellDetector().detect(_fixture())
    god = _by_smell(findings, "god_node")
    oversized = _by_smell(findings, "oversized_module")
    cyclic = _by_smell(findings, "cyclic_dependency")
    assert [f.node for f in god] == ["mod.core"]
    assert [f.node for f in oversized] == ["mod.big"]
    assert {f.node for f in cyclic} == {"mod.a", "mod.b", "mod.c"}
    assert _by_smell(findings, "spof") == []  # fan-in 6 < default spof threshold 15


def test_god_node_evidence_and_default_severity() -> None:
    god = _by_smell(SmellDetector().detect(_fixture()), "god_node")[0]
    assert god.node == "mod.core"
    assert god.evidence["fan_in"] == 6
    assert god.evidence["fan_out"] == 0
    assert god.severity == "low"  # ratio 0.545/0.5 = 1.09 < medium band 1.5


def test_oversized_evidence() -> None:
    oversized = _by_smell(SmellDetector().detect(_fixture()), "oversized_module")[0]
    assert oversized.evidence["loc"] == 420


def test_spof_detected_with_lower_threshold() -> None:
    cfg = SmellConfig(spof_fan_in=5)
    spof = _by_smell(SmellDetector(cfg).detect(_fixture()), "spof")
    assert "mod.core" in [f.node for f in spof]  # articulation point, fan-in 6 >= 5


def test_severity_bands() -> None:
    # oversized_loc=10 so mod.big (420) gives ratio 42 -> high; mod.db (120) -> high too
    cfg = SmellConfig(oversized_loc=200, severity_medium=1.5, severity_high=2.0)
    findings = _by_smell(SmellDetector(cfg).detect(_fixture()), "oversized_module")
    big = next(f for f in findings if f.node == "mod.big")
    assert big.severity == "high"  # 420/200 = 2.1 >= 2.0


def test_findings_sorted_by_severity_then_centrality() -> None:
    findings = SmellDetector(SmellConfig(spof_fan_in=5, oversized_loc=50)).detect(_fixture())
    ranks = {"high": 3, "medium": 2, "low": 1}
    severities = [ranks[f.severity] for f in findings]
    assert severities == sorted(severities, reverse=True)  # non-increasing


def test_self_loop_is_cyclic_low() -> None:
    graph = GraphModel("1.00", (Node("x", NodeType.MODULE),), (Edge("x", "x", EdgeKind.CALL),))
    findings = SmellDetector().detect(graph)
    cyclic = _by_smell(findings, "cyclic_dependency")
    assert len(cyclic) == 1
    assert cyclic[0].node == "x"
    assert cyclic[0].severity == "low"


def test_oversized_skipped_when_loc_absent() -> None:
    graph = GraphModel("1.00", (Node("x", NodeType.MODULE),), ())  # no loc
    assert _by_smell(SmellDetector().detect(graph), "oversized_module") == []


def test_smellconfig_from_dict_defaults_and_overrides() -> None:
    default = SmellConfig.from_dict({})
    assert default.god_node_centrality == 0.5
    assert default.severity_high == 2.0
    custom = SmellConfig.from_dict({"god_node_fan_in": 3, "severity_bands": {"high": 5.0}})
    assert custom.god_node_fan_in == 3
    assert custom.severity_high == 5.0


def test_god_node_by_fan_in_threshold() -> None:
    # a hub with fan-in 3, threshold 3 -> god node by fan-in even at low centrality
    nodes = tuple(Node(f"n{i}", NodeType.MODULE) for i in range(5))
    edges = tuple(Edge(f"n{i}", "n0", EdgeKind.IMPORT) for i in range(1, 4))
    cfg = SmellConfig(god_node_centrality=0.99, god_node_fan_in=3)
    god = _by_smell(SmellDetector(cfg).detect(GraphModel("1.00", nodes, edges)), "god_node")
    assert [f.node for f in god] == ["n0"]
