"""Reverse-engineer Markdown/Mermaid views from a graph (assignment §5.2, TODO 2.4).

Emits two diagrams from a :class:`GraphModel`:

- a **module block diagram** (Mermaid flowchart) — the main parts and the data flow
  (import/call edges) between them;
- an **OOP class map** (Mermaid classDiagram) — classes with inheritance and usage.

Both are returned as Markdown with embedded Mermaid, and are deterministic (sorted).
"""

from __future__ import annotations

from arch_agent.services.models import EdgeKind, GraphModel, NodeType


def _mid(node_id: str) -> str:
    """Map a node id to a Mermaid-safe identifier."""
    return "".join(c if c.isalnum() else "_" for c in node_id)


class ReverseEngineer:
    """Produce architecture diagrams from a :class:`GraphModel`."""

    def block_diagram(self, graph: GraphModel) -> str:
        """Mermaid flowchart of module nodes and the edges between them."""
        modules = {n.id for n in graph.nodes if n.type is NodeType.MODULE}
        nodes = [f'  {_mid(nid)}["{nid}"]' for nid in sorted(modules)]
        edges = sorted(
            f"  {_mid(e.src)} --> {_mid(e.dst)}"
            for e in graph.edges
            if e.src in modules and e.dst in modules
        )
        return "\n".join(["```mermaid", "flowchart LR", *nodes, *edges, "```"])

    def class_map(self, graph: GraphModel) -> str:
        """Mermaid class diagram: classes with inheritance (``<|--``) and usage (``-->``)."""
        classes = {n.id for n in graph.nodes if n.type is NodeType.CLASS}
        nodes = [f"  class {_mid(nid)}" for nid in sorted(classes)]
        relations: list[str] = []
        for edge in graph.edges:
            if edge.src not in classes:
                continue
            if edge.kind is EdgeKind.INHERIT:
                relations.append(f"  {_mid(edge.dst)} <|-- {_mid(edge.src)}")
            else:
                relations.append(f"  {_mid(edge.src)} --> {_mid(edge.dst)}")
        return "\n".join(["```mermaid", "classDiagram", *nodes, *sorted(relations), "```"])

    def render(self, graph: GraphModel) -> str:
        """Combine both diagrams into a single Markdown document."""
        return "\n\n".join(
            [
                "# Reverse-Engineered Architecture",
                "## Module Block Diagram",
                self.block_diagram(graph),
                "## OOP Class Map",
                self.class_map(graph),
            ]
        )
