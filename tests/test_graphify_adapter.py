"""Tests for :mod:`arch_agent.services.graphify_adapter` and loader integration."""

from __future__ import annotations

from arch_agent.services.graph_loader import GraphLoader
from arch_agent.services.graphify_adapter import is_graphify, normalize
from arch_agent.services.models import EdgeKind, NodeType

# Trimmed sample of graphify's real node-link output (NetworkX format).
_GRAPHIFY = {
    "directed": False,
    "multigraph": False,
    "graph": {},
    "nodes": [
        {"id": "main", "label": "main.py", "file_type": "code"},
        {"id": "snip_foo", "label": "foo()", "file_type": "code"},
        {"id": "svc", "label": "Service", "file_type": "code"},
        {"id": "why", "label": "The purpose of...", "file_type": "rationale"},
        {"label": "no-id"},
    ],
    "links": [
        {"source": "main", "target": "snip_foo"},
        {"source": "svc", "target": "main", "kind": "import"},
        {"source": "main", "target": "ghost"},  # dangling -> dropped
    ],
}


def test_is_graphify_detects_node_link() -> None:
    assert is_graphify(_GRAPHIFY)
    assert not is_graphify({"version": "1.00", "nodes": [], "edges": []})  # PLAN schema


def test_normalize_maps_nodes_and_infers_types() -> None:
    out = normalize(_GRAPHIFY)
    by_id = {n["id"]: n["type"] for n in out["nodes"]}
    assert by_id == {"main": "module", "snip_foo": "function", "svc": "class"}
    # rationale node and the id-less node are dropped
    assert "why" not in by_id


def test_normalize_maps_links_to_edges() -> None:
    edges = normalize(_GRAPHIFY)["edges"]
    pairs = {(e["src"], e["dst"], e["kind"]) for e in edges}
    assert ("main", "snip_foo", "call") in pairs  # default kind
    assert ("svc", "main", "import") in pairs  # recognised kind kept
    assert all(e["dst"] != "ghost" for e in edges)  # dangling dropped


def test_graphloader_parses_graphify_format() -> None:
    graph = GraphLoader().parse(_GRAPHIFY)
    assert graph.node_ids() == frozenset({"main", "snip_foo", "svc"})
    assert len(graph.edges) == 2
    types = {n.id: n.type for n in graph.nodes}
    assert types["snip_foo"] is NodeType.FUNCTION
    assert types["svc"] is NodeType.CLASS
    assert graph.edges[0].kind in (EdgeKind.CALL, EdgeKind.IMPORT)


def test_infer_type_defaults_to_module() -> None:
    out = normalize({"nodes": [{"id": "pkg", "label": "utils", "file_type": "code"}], "links": []})
    assert out["nodes"] == [{"id": "pkg", "type": "module"}]  # not .py / () / Cap -> module


def test_unknown_edge_kind_defaults_to_call() -> None:
    data = {
        "nodes": [{"id": "a", "label": "a.py", "file_type": "code"}, {"id": "b", "label": "b.py"}],
        "links": [{"source": "a", "target": "b", "kind": "telepathy"}],
    }
    edges = normalize(data)["edges"]
    assert edges == [{"src": "a", "dst": "b", "kind": "call"}]
