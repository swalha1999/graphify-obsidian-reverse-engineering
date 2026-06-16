"""Tests for :mod:`arch_agent.services.models`."""

from __future__ import annotations

import dataclasses

import pytest

from arch_agent.services.models import Edge, EdgeKind, GraphModel, Node, NodeType


def test_enum_values() -> None:
    assert NodeType.MODULE.value == "module"
    assert EdgeKind.INHERIT.value == "inherit"
    assert NodeType("class") is NodeType.CLASS


def test_node_defaults_and_optional_fields() -> None:
    n = Node(id="mod.a", type=NodeType.MODULE)
    assert n.loc is None
    assert n.centrality is None
    assert Node(id="mod.b", type=NodeType.MODULE, loc=10, centrality=0.5).loc == 10


def test_node_rejects_empty_id() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        Node(id="", type=NodeType.MODULE)


def test_node_rejects_negative_loc() -> None:
    with pytest.raises(ValueError, match="negative loc"):
        Node(id="mod.a", type=NodeType.MODULE, loc=-1)


def test_node_is_frozen() -> None:
    n = Node(id="mod.a", type=NodeType.MODULE)
    with pytest.raises(dataclasses.FrozenInstanceError):
        n.id = "x"  # type: ignore[misc]


def test_edge_valid_and_rejects_empty_endpoints() -> None:
    assert Edge(src="a", dst="b", kind=EdgeKind.IMPORT).kind is EdgeKind.IMPORT
    with pytest.raises(ValueError, match="endpoints"):
        Edge(src="a", dst="", kind=EdgeKind.CALL)


def _graph() -> GraphModel:
    nodes = (Node("a", NodeType.MODULE), Node("b", NodeType.MODULE))
    edges = (Edge("a", "b", EdgeKind.IMPORT),)
    return GraphModel(version="1.00", nodes=nodes, edges=edges)


def test_graph_node_ids() -> None:
    assert _graph().node_ids() == frozenset({"a", "b"})


def test_graph_rejects_empty_version() -> None:
    with pytest.raises(ValueError, match="version"):
        GraphModel(version="", nodes=(), edges=())


def test_graph_rejects_duplicate_node_ids() -> None:
    nodes = (Node("a", NodeType.MODULE), Node("a", NodeType.CLASS))
    with pytest.raises(ValueError, match="duplicate"):
        GraphModel(version="1.00", nodes=nodes, edges=())


def test_dangling_edges() -> None:
    nodes = (Node("a", NodeType.MODULE),)
    edges = (Edge("a", "ghost", EdgeKind.CALL), Edge("a", "a", EdgeKind.CALL))
    g = GraphModel(version="1.00", nodes=nodes, edges=edges)
    dangling = g.dangling_edges()
    assert len(dangling) == 1
    assert dangling[0].dst == "ghost"
