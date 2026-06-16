"""Tests for :mod:`arch_agent.services.cycles`."""

from __future__ import annotations

from pathlib import Path

from arch_agent.services.cycles import find_cycles, find_self_loops
from arch_agent.services.graph_loader import GraphLoader
from arch_agent.services.models import Edge, EdgeKind, GraphModel, Node, NodeType

FIXTURE = Path(__file__).parent / "fixtures" / "graph.json"


def _graph(node_ids: list[str], edges: list[tuple[str, str]]) -> GraphModel:
    nodes = tuple(Node(i, NodeType.MODULE) for i in node_ids)
    es = tuple(Edge(s, d, EdgeKind.IMPORT) for s, d in edges)
    return GraphModel("1.00", nodes, es)


def test_detects_fixture_cycle() -> None:
    graph = GraphLoader().load(FIXTURE)
    assert find_cycles(graph) == [["mod.a", "mod.b", "mod.c"]]
    assert find_self_loops(graph) == []


def test_no_cycle_in_dag() -> None:
    assert find_cycles(_graph(["a", "b", "c"], [("a", "b"), ("b", "c")])) == []


def test_two_independent_cycles_sorted() -> None:
    graph = _graph(["a", "b", "c", "d"], [("a", "b"), ("b", "a"), ("c", "d"), ("d", "c")])
    assert find_cycles(graph) == [["a", "b"], ["c", "d"]]


def test_self_loop_reported_separately_not_as_cycle() -> None:
    graph = _graph(["x", "y"], [("x", "x"), ("x", "y")])
    assert find_self_loops(graph) == ["x"]
    assert find_cycles(graph) == []  # a self-loop is not an SCC of size > 1


def test_dangling_edges_ignored() -> None:
    # both endpoints reference a non-node, so no real cycle forms
    graph = _graph(["a"], [("a", "ghost"), ("ghost", "a")])
    assert find_cycles(graph) == []


def test_longer_cycle_and_tail() -> None:
    # cycle a->b->c->d->a with a tail e->a (e not part of the cycle)
    graph = _graph(
        ["a", "b", "c", "d", "e"],
        [("a", "b"), ("b", "c"), ("c", "d"), ("d", "a"), ("e", "a")],
    )
    assert find_cycles(graph) == [["a", "b", "c", "d"]]
