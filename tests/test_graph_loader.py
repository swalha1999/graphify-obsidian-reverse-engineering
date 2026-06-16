"""Tests for :mod:`arch_agent.services.graph_loader`."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from arch_agent.services.graph_loader import GraphLoader
from arch_agent.services.models import EdgeKind, NodeType

FIXTURE = Path(__file__).parent / "fixtures" / "graph.json"


def test_load_real_fixture() -> None:
    graph = GraphLoader().load(FIXTURE)
    assert graph.version == "1.00"
    assert len(graph.nodes) == 12
    assert len(graph.edges) == 14
    assert "mod.core" in graph.node_ids()
    assert graph.dangling_edges() == ()


def test_load_reads_file(tmp_path: Path) -> None:
    p = tmp_path / "graph.json"
    p.write_text(json.dumps({"nodes": [{"id": "a", "type": "module"}], "edges": []}))
    assert GraphLoader().load(p).node_ids() == frozenset({"a"})


def test_missing_version_defaults() -> None:
    assert GraphLoader().parse({"nodes": [], "edges": []}).version == "0.0"


def test_non_object_raises() -> None:
    with pytest.raises(ValueError, match="must be a JSON object"):
        GraphLoader().parse([1, 2, 3])


def test_unknown_type_and_kind_skipped() -> None:
    data: dict[str, Any] = {
        "nodes": [
            {"id": "a", "type": "module"},
            {"id": "b", "type": "wormhole"},  # unknown type -> skipped
            {"type": "module"},  # missing id -> skipped
            "not-a-dict",
        ],
        "edges": [
            {"src": "a", "dst": "a", "kind": "import"},
            {"src": "a", "dst": "a", "kind": "telepathy"},  # unknown kind -> skipped
            {"src": "a", "kind": "call"},  # missing dst -> skipped
            "not-a-dict-edge",  # non-dict -> skipped
        ],
    }
    graph = GraphLoader().parse(data)
    assert graph.node_ids() == frozenset({"a"})
    assert len(graph.edges) == 1


def test_unknown_fields_ignored_and_optionals() -> None:
    node = {"id": "a", "type": "module", "loc": 5, "centrality": 0.5, "extra": "x"}
    graph = GraphLoader().parse({"version": "1.00", "nodes": [node], "edges": []})
    only = graph.nodes[0]
    assert only.loc == 5
    assert only.centrality == 0.5


@pytest.mark.parametrize("bad_loc", [-1, True, "10", 1.5, None])
def test_invalid_loc_becomes_none(bad_loc: Any) -> None:
    graph = GraphLoader().parse(
        {"nodes": [{"id": "a", "type": "module", "loc": bad_loc}], "edges": []}
    )
    assert graph.nodes[0].loc is None


@pytest.mark.parametrize(("raw", "expected"), [(1, 1.0), (0.25, 0.25), (True, None), ("x", None)])
def test_centrality_coercion(raw: Any, expected: float | None) -> None:
    graph = GraphLoader().parse(
        {"nodes": [{"id": "a", "type": "module", "centrality": raw}], "edges": []}
    )
    assert graph.nodes[0].centrality == expected


def test_nodes_edges_not_a_list_treated_empty() -> None:
    graph = GraphLoader().parse({"nodes": "oops", "edges": None})
    assert graph.nodes == ()
    assert graph.edges == ()


def test_dangling_edge_kept() -> None:
    data = {
        "nodes": [{"id": "a", "type": "module"}],
        "edges": [{"src": "a", "dst": "ghost", "kind": "call"}],
    }
    graph = GraphLoader().parse(data)
    assert len(graph.edges) == 1
    assert graph.edges[0].kind is EdgeKind.CALL
    assert len(graph.dangling_edges()) == 1


def test_fixture_node_types_parsed() -> None:
    graph = GraphLoader().load(FIXTURE)
    by_id = {n.id: n for n in graph.nodes}
    assert by_id["class.Service"].type is NodeType.CLASS
    assert by_id["func.helper"].type is NodeType.FUNCTION
