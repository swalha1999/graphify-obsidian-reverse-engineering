"""Tests for :mod:`arch_agent.services.impact` (blast radius + orphans, FR-17).

Expected values are hand-computed on small constructed graphs. ``src`` depends on
``dst``; blast radius = transitive *dependents* (who breaks if this node breaks).
"""

from __future__ import annotations

from arch_agent.services.impact import ImpactAnalyzer
from arch_agent.services.models import Edge, EdgeKind, GraphModel, Node, NodeType


def _graph(node_ids: list[str], edges: list[tuple[str, str]]) -> GraphModel:
    return GraphModel(
        version="1.00",
        nodes=tuple(Node(id=i, type=NodeType.MODULE) for i in node_ids),
        edges=tuple(Edge(src=s, dst=d, kind=EdgeKind.CALL) for s, d in edges),
    )


def test_blast_radius_chain_counts_transitive_dependents() -> None:
    # a -> b -> c -> d : everyone upstream depends (transitively) on d.
    g = _graph(["a", "b", "c", "d"], [("a", "b"), ("b", "c"), ("c", "d")])
    impact = ImpactAnalyzer(g)
    assert impact.blast_radius("d") == frozenset({"a", "b", "c"})
    assert impact.blast_radius("c") == frozenset({"a", "b"})
    assert impact.blast_radius("a") == frozenset()  # nothing depends on a


def test_blast_radius_unknown_node_is_empty() -> None:
    g = _graph(["a", "b"], [("a", "b")])
    assert ImpactAnalyzer(g).blast_radius("nope") == frozenset()


def test_blast_radius_excludes_self_in_cycle() -> None:
    # a -> b -> a : each depends on the other, but a node is never in its own radius.
    g = _graph(["a", "b"], [("a", "b"), ("b", "a")])
    impact = ImpactAnalyzer(g)
    assert impact.blast_radius("a") == frozenset({"b"})
    assert impact.blast_radius("b") == frozenset({"a"})


def test_blast_radius_ignores_dangling_edges() -> None:
    # Edge into a non-node must not bridge or inflate the radius.
    g = _graph(["a", "b"], [("a", "b"), ("ghost", "b")])
    assert ImpactAnalyzer(g).blast_radius("b") == frozenset({"a"})


def test_blast_radii_sorted_by_impact_then_id() -> None:
    g = _graph(["a", "b", "c", "d"], [("a", "b"), ("b", "c"), ("c", "d")])
    radii = ImpactAnalyzer(g).blast_radii()
    assert list(radii.items()) == [("d", 3), ("c", 2), ("b", 1), ("a", 0)]


def test_orphans_are_fully_isolated_nodes() -> None:
    # 'lonely' has no edges; 'a'/'b' are connected.
    g = _graph(["a", "b", "lonely"], [("a", "b")])
    assert ImpactAnalyzer(g).orphans() == frozenset({"lonely"})


def test_no_orphans_when_all_connected() -> None:
    g = _graph(["a", "b"], [("a", "b")])
    assert ImpactAnalyzer(g).orphans() == frozenset()
