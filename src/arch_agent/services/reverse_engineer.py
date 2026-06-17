"""Reverse-engineer Markdown/Mermaid views from a graph (assignment §5.2, TODO 2.4).

Emits, from a :class:`GraphModel`, a self-contained architecture document:

- an **overview** — node/edge counts and the key structural facts (most central
  nodes, single points of failure, blast radius, cycles), derived from the metrics;
- a **block & call graph** (Mermaid flowchart) — modules as containers, the
  functions inside each, and every dependency edge between them;
- an **OOP class map** (Mermaid classDiagram) — classes with inheritance and usage,
  or a note when the codebase has no classes.

Everything is deterministic (sorted) and a pure function of the graph.
"""

from __future__ import annotations

from collections import Counter

from arch_agent.services.cycles import find_cycles
from arch_agent.services.impact import ImpactAnalyzer
from arch_agent.services.metrics import MetricsCalculator
from arch_agent.services.models import EdgeKind, GraphModel, Node, NodeType


def _mid(node_id: str) -> str:
    """Map a node id to a Mermaid-safe identifier."""
    return "".join(c if c.isalnum() else "_" for c in node_id)


def _parent_module(node_id: str, module_ids: set[str]) -> str | None:
    """Return the longest module id that is a ``<module>_`` prefix of ``node_id``."""
    candidates = [m for m in module_ids if node_id.startswith(f"{m}_")]
    return max(candidates, key=len) if candidates else None


def _short_label(node_id: str, parent: str | None) -> str:
    """Strip the parent-module prefix for a compact label (``a_b_foo`` -> ``foo``)."""
    return node_id[len(parent) + 1 :] if parent else node_id


class ReverseEngineer:
    """Produce architecture diagrams from a :class:`GraphModel`."""

    def overview(self, graph: GraphModel) -> str:
        """A counts table plus the key structural facts, derived from the metrics."""
        counts = Counter(n.type for n in graph.nodes)
        kinds = Counter(e.kind.value for e in graph.edges)
        metrics = MetricsCalculator(graph)
        centrality = metrics.centrality()
        articulations = metrics.articulation_points()
        impact = ImpactAnalyzer(graph)
        radii = impact.blast_radii()
        orphans = impact.orphans()
        cycles = find_cycles(graph)

        edge_kinds = ", ".join(f"{n} {k}" for k, n in sorted(kinds.items())) or "none"
        table = [
            "| Metric | Value |",
            "|---|---|",
            f"| Modules | {counts[NodeType.MODULE]} |",
            f"| Classes | {counts[NodeType.CLASS]} |",
            f"| Functions | {counts[NodeType.FUNCTION]} |",
            f"| Dependencies | {len(graph.edges)} ({edge_kinds}) |",
        ]

        facts: list[str] = []
        top = [
            (nid, v)
            for nid, v in sorted(centrality.items(), key=lambda kv: (-kv[1], kv[0]))
            if v > 0
        ][:3]
        if top:
            facts.append("- **Most central:** " + ", ".join(f"`{n}` ({v:.2f})" for n, v in top))
        if articulations:
            facts.append(
                "- **Single points of failure (articulation points):** "
                + ", ".join(f"`{a}`" for a in sorted(articulations))
            )
        blast = [(nid, s) for nid, s in radii.items() if s > 0][:3]
        if blast:
            facts.append(
                "- **Highest blast radius:** " + ", ".join(f"`{n}` ({s})" for n, s in blast)
            )
        facts.append(
            f"- **Dependency cycles:** {len(cycles)} found"
            if cycles
            else "- **Dependency cycles:** none"
        )
        if orphans:
            facts.append("- **Orphan components:** " + ", ".join(f"`{o}`" for o in sorted(orphans)))

        return "\n".join([*table, "", *facts])

    def block_diagram(self, graph: GraphModel) -> str:
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
                lines.append(f'  subgraph {_mid(module_id)}["{module_id}"]')
                for fn in sorted(kids, key=lambda n: n.id):
                    lines.append(f'    {_mid(fn.id)}["{_short_label(fn.id, module_id)}"]')
                lines.append("  end")
            else:
                lines.append(f'  {_mid(module_id)}["{module_id}"]')
        for fn in sorted(top_level, key=lambda n: n.id):
            lines.append(f'  {_mid(fn.id)}["{fn.id}"]')

        edges = sorted(
            f"  {_mid(e.src)} --> {_mid(e.dst)}"
            for e in graph.edges
            if e.src in shown and e.dst in shown
        )
        lines.extend(edges)
        lines.append("```")
        return "\n".join(lines)

    def class_map(self, graph: GraphModel) -> str:
        """Mermaid class diagram: classes with inheritance (``<|--``) and usage (``-->``).

        Returns a Markdown note (not a Mermaid block) when the graph has no classes —
        an empty ``classDiagram`` is a Mermaid parse error, so a module/function-only
        codebase must not emit one.
        """
        classes = {n.id for n in graph.nodes if n.type is NodeType.CLASS}
        if not classes:
            return "_No classes found — this codebase is module/function-only._"
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
        """Combine overview + both diagrams into a single Markdown document."""
        return "\n\n".join(
            [
                "# Reverse-Engineered Architecture",
                "## Overview",
                self.overview(graph),
                "## Block & Call Graph",
                self.block_diagram(graph),
                "## OOP Class Map",
                self.class_map(graph),
            ]
        )
