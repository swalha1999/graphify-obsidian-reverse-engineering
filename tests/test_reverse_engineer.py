"""Tests for :mod:`arch_agent.services.reverse_engineer`."""

from __future__ import annotations

from pathlib import Path

from arch_agent.services.graph_loader import GraphLoader
from arch_agent.services.models import Edge, EdgeKind, GraphModel, Node, NodeType
from arch_agent.services.reverse_engineer import ReverseEngineer, _mid

FIXTURE = Path(__file__).parent / "fixtures" / "graph.json"


def _fixture() -> GraphModel:
    return GraphLoader().load(FIXTURE)


def test_mid_sanitizes() -> None:
    assert _mid("mod.core") == "mod_core"
    assert _mid("class.Service") == "class_Service"


def test_block_diagram_includes_functions_excludes_classes() -> None:
    out = ReverseEngineer().block_diagram(_fixture())
    assert out.startswith("```mermaid\nflowchart LR")
    assert out.endswith("```")
    assert '  mod_core["mod.core"]' in out
    assert "  mod_api --> mod_core" in out
    # func.helper has no parent module -> shown as a top-level node.
    assert '  func_helper["func.helper"]' in out
    # classes belong to the OOP map, not the block diagram.
    assert "class_Service" not in out


def test_block_diagram_groups_functions_under_module() -> None:
    nodes = (
        Node("pkg_mod", NodeType.MODULE),
        Node("pkg_mod_run", NodeType.FUNCTION),
    )
    edges = (Edge("pkg_mod", "pkg_mod_run", EdgeKind.CALL),)
    out = ReverseEngineer().block_diagram(GraphModel("1.00", nodes, edges))
    assert '  subgraph pkg_mod["pkg_mod"]' in out
    assert '    pkg_mod_run["run"]' in out  # prefix stripped for a compact label
    assert "  end" in out
    assert "  pkg_mod --> pkg_mod_run" in out


def test_overview_counts_and_key_facts() -> None:
    out = ReverseEngineer().overview(_fixture())
    assert "| Modules | 9 |" in out
    assert "| Classes | 2 |" in out
    assert "| Functions | 1 |" in out
    assert "**Most central:**" in out
    assert "**Dependency cycles:** 1 found" in out  # mod.a -> mod.b -> mod.c -> mod.a


def test_overview_orphans_and_no_cycles() -> None:
    nodes = (
        Node("pkg_a", NodeType.MODULE),
        Node("pkg_a_run", NodeType.FUNCTION),
        Node("pkg_b", NodeType.MODULE),  # isolated -> orphan
    )
    edges = (Edge("pkg_a", "pkg_a_run", EdgeKind.CALL),)
    out = ReverseEngineer().overview(GraphModel("1.00", nodes, edges))
    assert "**Dependency cycles:** none" in out
    assert "**Highest blast radius:**" in out
    assert "**Orphan components:** `pkg_b`" in out


def test_overview_edgeless_graph_has_no_centrality_or_blast_facts() -> None:
    # A lone node: centrality and blast radius are all zero, so those facts are omitted.
    out = ReverseEngineer().overview(GraphModel("1.00", (Node("solo", NodeType.MODULE),), ()))
    assert "**Most central:**" not in out
    assert "**Highest blast radius:**" not in out
    assert "**Orphan components:** `solo`" in out


def test_class_map_inheritance_and_usage() -> None:
    out = ReverseEngineer().class_map(_fixture())
    assert out.startswith("```mermaid\nclassDiagram")
    assert "  class class_Service" in out
    assert "  class class_Base" in out
    assert "  class_Base <|-- class_Service" in out  # Service inherits Base
    assert "  class_Service --> mod_core" in out  # Service uses core (call)


def test_render_combines_sections() -> None:
    out = ReverseEngineer().render(_fixture())
    assert "## Overview" in out
    assert "## Block & Call Graph" in out
    assert "## OOP Class Map" in out
    assert out.count("```mermaid") == 2  # block diagram + class map (fixture has classes)


def test_deterministic() -> None:
    rev = ReverseEngineer()
    graph = _fixture()
    assert rev.render(graph) == rev.render(graph)


def test_empty_graph() -> None:
    empty = GraphModel("1.00", (), ())
    assert ReverseEngineer().block_diagram(empty) == "```mermaid\nflowchart LR\n```"
    # No classes -> a note, not an empty classDiagram (which Mermaid rejects).
    assert ReverseEngineer().class_map(empty) == (
        "_No classes found — this codebase is module/function-only._"
    )


def test_class_map_note_when_no_classes() -> None:
    # A module/function-only graph (like the buggy-python target) must not emit
    # an empty ```mermaid classDiagram``` block.
    nodes = (Node("mod.a", NodeType.MODULE), Node("func.f", NodeType.FUNCTION))
    out = ReverseEngineer().class_map(GraphModel("1.00", nodes, ()))
    assert "classDiagram" not in out
    assert out.startswith("_No classes found")


def test_class_inherit_between_two_classes() -> None:
    nodes = (Node("class.A", NodeType.CLASS), Node("class.B", NodeType.CLASS))
    edges = (Edge("class.B", "class.A", EdgeKind.INHERIT),)
    out = ReverseEngineer().class_map(GraphModel("1.00", nodes, edges))
    assert "  class_A <|-- class_B" in out
