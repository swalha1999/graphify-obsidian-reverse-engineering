"""Tests for :mod:`arch_agent.services.metrics`.

Expected values for the fixture are hand-computed (PRD_graph_analysis §3, TODO 2.1).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from arch_agent.services.graph_loader import GraphLoader
from arch_agent.services.metrics import MetricsCalculator
from arch_agent.services.models import Edge, EdgeKind, GraphModel, Node, NodeType

FIXTURE = Path(__file__).parent / "fixtures" / "graph.json"


def _fixture() -> MetricsCalculator:
    return MetricsCalculator(GraphLoader().load(FIXTURE))


def test_fan_in_matches_hand_computed() -> None:
    fan_in = _fixture().fan_in()
    assert fan_in["mod.core"] == 6  # api, db, util, big, a, Service
    assert fan_in["mod.api"] == 1
    assert fan_in["mod.cli"] == 0
    assert sum(fan_in.values()) == 14  # every edge has a node dst


def test_fan_out_matches_hand_computed() -> None:
    fan_out = _fixture().fan_out()
    assert fan_out["class.Service"] == 3  # -> core, Base, helper
    assert fan_out["mod.api"] == 2  # -> core, db
    assert fan_out["mod.core"] == 0
    assert sum(fan_out.values()) == 14


def test_centrality_normalised() -> None:
    centrality = _fixture().centrality()
    assert centrality["mod.core"] == pytest.approx(6 / 11)
    assert centrality["mod.api"] == pytest.approx(3 / 11)
    assert all(0.0 <= v <= 1.0 for v in centrality.values())


def test_centrality_single_node_is_zero() -> None:
    graph = GraphModel("1.00", (Node("x", NodeType.MODULE),), ())
    assert MetricsCalculator(graph).centrality() == {"x": 0.0}


def test_proximity_hops_from_core() -> None:
    dist = _fixture().proximity({"mod.core"})
    assert dist["mod.core"] == 0
    assert dist["mod.api"] == 1
    assert dist["mod.cli"] == 2  # core -> api -> cli
    assert dist["func.helper"] == 2  # core -> Service -> helper
    assert len(dist) == 12  # whole graph is connected (undirected)


def test_proximity_ignores_unknown_seed() -> None:
    assert _fixture().proximity({"ghost"}) == {}


def test_proximity_score_reachable_and_unreachable() -> None:
    nodes = (Node("a", NodeType.MODULE), Node("b", NodeType.MODULE), Node("c", NodeType.MODULE))
    edges = (Edge("a", "b", EdgeKind.IMPORT),)  # c is isolated
    score = MetricsCalculator(GraphModel("1.00", nodes, edges)).proximity_score({"a"})
    assert score["a"] == 1.0
    assert score["b"] == pytest.approx(0.5)
    assert score["c"] == 0.0


def test_dangling_edge_does_not_bridge_nodes() -> None:
    nodes = (Node("a", NodeType.MODULE), Node("b", NodeType.MODULE))
    edges = (Edge("a", "ghost", EdgeKind.CALL), Edge("ghost", "b", EdgeKind.CALL))
    dist = MetricsCalculator(GraphModel("1.00", nodes, edges)).proximity({"a"})
    assert dist == {"a": 0}  # ghost is not a node, so a and b stay disconnected


def test_fan_in_out_skip_dangling_endpoints() -> None:
    nodes = (Node("a", NodeType.MODULE), Node("b", NodeType.MODULE))
    edges = (Edge("a", "ghost", EdgeKind.CALL), Edge("ghost", "b", EdgeKind.CALL))
    mc = MetricsCalculator(GraphModel("1.00", nodes, edges))
    assert mc.fan_in() == {"a": 0, "b": 1}  # a->ghost dst ignored; ghost->b counts to b
    assert mc.fan_out() == {"a": 1, "b": 0}  # ghost->b src ignored; a->ghost counts from a
