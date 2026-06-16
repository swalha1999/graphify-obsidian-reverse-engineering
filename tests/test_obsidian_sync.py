"""Tests for :mod:`arch_agent.services.obsidian_sync`."""

from __future__ import annotations

from pathlib import Path

from arch_agent.services.graph_loader import GraphLoader
from arch_agent.services.models import Edge, EdgeKind, GraphModel, Node, NodeType
from arch_agent.services.obsidian_sync import ObsidianSync, _link, _slug

FIXTURE = Path(__file__).parent / "fixtures" / "graph.json"


def _small() -> GraphModel:
    nodes = (
        Node("mod.a", NodeType.MODULE, loc=10),
        Node("mod.b", NodeType.MODULE, centrality=0.4),
    )
    edges = (Edge("mod.a", "mod.b", EdgeKind.IMPORT),)
    return GraphModel(version="1.00", nodes=nodes, edges=edges)


def test_slug_sanitizes_invalid_chars() -> None:
    assert _slug("a/b:c*d") == "a_b_c_d"
    assert _slug("mod.core") == "mod.core"


def test_link_format() -> None:
    assert _link("mod.core") == "[[mod.core|mod.core]]"


def test_write_creates_expected_files(tmp_path: Path) -> None:
    vault = ObsidianSync().write(_small(), tmp_path / "vault")
    assert (vault / "index.md").is_file()
    assert (vault / "hot.md").is_file()
    assert (vault / "nodes" / "mod.a.md").is_file()
    assert (vault / "nodes" / "mod.b.md").is_file()


def test_note_contents(tmp_path: Path) -> None:
    vault = ObsidianSync().write(_small(), tmp_path / "vault")
    a = (vault / "nodes" / "mod.a.md").read_text(encoding="utf-8")
    b = (vault / "nodes" / "mod.b.md").read_text(encoding="utf-8")
    assert "- type: module" in a
    assert "- loc: 10" in a
    assert "[[mod.b|mod.b]]" in a  # a depends on b
    assert "- centrality: 0.4" in b
    assert "[[mod.a|mod.a]]" in b  # b depended on by a


def test_index_groups_present_types_only(tmp_path: Path) -> None:
    vault = ObsidianSync().write(_small(), tmp_path / "vault")
    index = (vault / "index.md").read_text(encoding="utf-8")
    assert "- nodes: 2" in index
    assert "## Modules" in index
    assert "Classs" not in index and "Functions" not in index  # absent types skipped


def test_hot_default_ranks_by_fan_in(tmp_path: Path) -> None:
    vault = ObsidianSync().write(GraphLoader().load(FIXTURE), tmp_path / "vault")
    hot = (vault / "hot.md").read_text(encoding="utf-8")
    assert "mod.core" in hot  # highest fan-in in the fixture
    assert "fan-in 6" in hot


def test_hot_nodes_override(tmp_path: Path) -> None:
    vault = ObsidianSync().write(_small(), tmp_path / "vault", hot_nodes=["mod.a"])
    hot = (vault / "hot.md").read_text(encoding="utf-8")
    assert "[[mod.a|mod.a]]" in hot


def test_hot_empty_when_no_edges(tmp_path: Path) -> None:
    graph = GraphModel(version="1.00", nodes=(Node("x", NodeType.MODULE),), edges=())
    vault = ObsidianSync().write(graph, tmp_path / "vault")
    assert "- (none)" in (vault / "hot.md").read_text(encoding="utf-8")
