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


def test_block_diagram_has_modules_and_edges_only() -> None:
    out = ReverseEngineer().block_diagram(_fixture())
    assert out.startswith("```mermaid\nflowchart LR")
    assert out.endswith("```")
    assert '  mod_core["mod.core"]' in out
    assert "  mod_api --> mod_core" in out
    # classes/functions are not part of the module block diagram
    assert "class_Service" not in out
    assert "func_helper" not in out


def test_class_map_inheritance_and_usage() -> None:
    out = ReverseEngineer().class_map(_fixture())
    assert out.startswith("```mermaid\nclassDiagram")
    assert "  class class_Service" in out
    assert "  class class_Base" in out
    assert "  class_Base <|-- class_Service" in out  # Service inherits Base
    assert "  class_Service --> mod_core" in out  # Service uses core (call)


def test_render_combines_both() -> None:
    out = ReverseEngineer().render(_fixture())
    assert "## Module Block Diagram" in out
    assert "## OOP Class Map" in out
    assert out.count("```mermaid") == 2


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
