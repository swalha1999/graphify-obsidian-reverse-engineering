"""Reverse-engineer Markdown/Mermaid views from a graph (assignment §5.2, TODO 2.4).

Emits, from a :class:`GraphModel`, a self-contained architecture document:

- an **overview** — node/edge counts and the key structural facts (most central
  nodes, single points of failure, blast radius, cycles), derived from the metrics;
- a **block & call graph** (Mermaid flowchart) — modules as containers, the
  functions inside each, and every dependency edge between them;
- an **OOP class map** (Mermaid classDiagram) — classes with inheritance and usage,
  or a note when the codebase has no classes.

The Mermaid drawing detail lives in :mod:`arch_agent.services.mermaid`; this module
orchestrates the overview and assembles the final document. Everything is
deterministic (sorted) and a pure function of the graph.
"""

from __future__ import annotations

from collections import Counter

from arch_agent.services.cycles import find_cycles
from arch_agent.services.impact import ImpactAnalyzer
from arch_agent.services.mermaid import block_diagram, class_map
from arch_agent.services.metrics import MetricsCalculator
from arch_agent.services.models import GraphModel, NodeType


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
        """Mermaid flowchart of functions grouped inside their module (see :mod:`mermaid`)."""
        return block_diagram(graph)

    def class_map(self, graph: GraphModel) -> str:
        """Mermaid class diagram with inheritance and usage (see :mod:`mermaid`)."""
        return class_map(graph)

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
