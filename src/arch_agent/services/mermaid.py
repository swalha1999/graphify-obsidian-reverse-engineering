"""Mermaid diagram builders for the reverse-engineered architecture views.

Pure, deterministic functions that turn a :class:`GraphModel` into Mermaid
source. Kept apart from :mod:`reverse_engineer` so that module stays focused on
*orchestration* (overview + assembling the document) while the diagram-drawing
detail — id sanitising, module grouping, edge rendering — lives here.

- :func:`block_diagram` — a ``flowchart`` of functions grouped inside modules;
- :func:`class_map` — a ``classDiagram`` of classes with inheritance and usage.
"""

from __future__ import annotations

from arch_agent.services.models import EdgeKind, GraphModel, Node, NodeType


def mermaid_id(node_id: str) -> str:
    """Map a node id to a Mermaid-safe identifier."""
    return "".join(c if c.isalnum() else "_" for c in node_id)


def _parent_module(node_id: str, module_ids: set[str]) -> str | None:
    """Return the longest module id that is a ``<module>_`` prefix of ``node_id``."""
    candidates = [m for m in module_ids if node_id.startswith(f"{m}_")]
    return max(candidates, key=len) if candidates else None


def _short_label(node_id: str, parent: str | None) -> str:
    """Strip the parent-module prefix for a compact label (``a_b_foo`` -> ``foo``)."""
    return node_id[len(parent) + 1 :] if parent else node_id


def block_diagram(graph: GraphModel) -> str:
    """Mermaid flowchart: functions grouped inside their module, with every edge.

    Modules become ``subgraph`` containers holding the functions whose ids are
    prefixed by the module id; modules and functions with no parent are top-level
    nodes. Classes are omitted here — they belong to the OOP class map. Every
    edge between two shown nodes is drawn.
    """
    modules = {n.id for n in graph.nodes if n.type is NodeType.MODULE}
    shown = {n.id for n in graph.nodes if n.type in (NodeType.MODULE, NodeType.FUNCTION)}
    functions = [n for n in graph.nodes if n.type is NodeType.FUNCTION]

    # Group each function under its parent module (if any).
    children: dict[str, list[Node]] = {m: [] for m in modules}
    top_level: list[Node] = []
    for fn in functions:
        parent = _parent_module(fn.id, modules)
        (children[parent].append(fn) if parent is not None else top_level.append(fn))

    lines: list[str] = ["```mermaid", "flowchart LR"]
    for module_id in sorted(modules):
        kids = children[module_id]
        if kids:
            lines.append(f'  subgraph {mermaid_id(module_id)}["{module_id}"]')
            for fn in sorted(kids, key=lambda n: n.id):
                lines.append(f'    {mermaid_id(fn.id)}["{_short_label(fn.id, module_id)}"]')
            lines.append("  end")
        else:
            lines.append(f'  {mermaid_id(module_id)}["{module_id}"]')
    for fn in sorted(top_level, key=lambda n: n.id):
        lines.append(f'  {mermaid_id(fn.id)}["{fn.id}"]')

    edges = sorted(
        f"  {mermaid_id(e.src)} --> {mermaid_id(e.dst)}"
        for e in graph.edges
        if e.src in shown and e.dst in shown
    )
    lines.extend(edges)
    lines.append("```")
    return "\n".join(lines)


def class_map(graph: GraphModel) -> str:
    """Mermaid class diagram: classes with inheritance (``<|--``) and usage (``-->``).

    Returns a Markdown note (not a Mermaid block) when the graph has no classes —
    an empty ``classDiagram`` is a Mermaid parse error, so a module/function-only
    codebase must not emit one.
    """
    classes = {n.id for n in graph.nodes if n.type is NodeType.CLASS}
    if not classes:
        return "_No classes found — this codebase is module/function-only._"
    nodes = [f"  class {mermaid_id(nid)}" for nid in sorted(classes)]
    relations: list[str] = []
    for edge in graph.edges:
        if edge.src not in classes:
            continue
        if edge.kind is EdgeKind.INHERIT:
            relations.append(f"  {mermaid_id(edge.dst)} <|-- {mermaid_id(edge.src)}")
        else:
            relations.append(f"  {mermaid_id(edge.src)} --> {mermaid_id(edge.dst)}")
    return "\n".join(["```mermaid", "classDiagram", *nodes, *sorted(relations), "```"])
