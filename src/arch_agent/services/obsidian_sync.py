"""Render a :class:`GraphModel` into a browsable Obsidian vault.

Writes one note per node under ``nodes/`` plus ``index.md`` (entry point) and
``hot.md`` (high-fan-in nodes worth attention) — PRD FR-4, PLAN §1.4. Notes link
to their dependencies with Obsidian ``[[wikilinks]]`` so the app's graph view
renders the structure.

``hot.md`` ranks by fan-in by default; a caller may pass ``hot_nodes`` (e.g. the
``MetricsCalculator`` ranking, TODO 2.1) to override that ordering.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from arch_agent.services.models import GraphModel, Node, NodeType

_INVALID = '<>:"/\\|?*'
_HOT_LIMIT = 10


def _slug(node_id: str) -> str:
    """Map a node id to a filesystem-safe note name."""
    return "".join("_" if c in _INVALID else c for c in node_id)


def _link(node_id: str) -> str:
    """An Obsidian wikilink to a node's note, aliased to its id."""
    return f"[[{_slug(node_id)}|{node_id}]]"


class ObsidianSync:
    """Write a GraphModel into an Obsidian vault directory."""

    def write(
        self, graph: GraphModel, vault_dir: Path, hot_nodes: Sequence[str] | None = None
    ) -> Path:
        """Write node notes + ``index.md`` + ``hot.md``; return ``vault_dir``."""
        nodes_dir = vault_dir / "nodes"
        nodes_dir.mkdir(parents=True, exist_ok=True)
        for node in graph.nodes:
            note = nodes_dir / f"{_slug(node.id)}.md"
            note.write_text(self._note(graph, node), encoding="utf-8")
        (vault_dir / "index.md").write_text(self._index(graph), encoding="utf-8")
        hot = list(hot_nodes) if hot_nodes is not None else self._rank(graph)
        (vault_dir / "hot.md").write_text(self._hot(graph, hot), encoding="utf-8")
        return vault_dir

    def _note(self, graph: GraphModel, node: Node) -> str:
        head = [f"# {node.id}", "", f"- type: {node.type.value}"]
        if node.loc is not None:
            head.append(f"- loc: {node.loc}")
        if node.centrality is not None:
            head.append(f"- centrality: {node.centrality}")
        head.append("")
        deps = [e.dst for e in graph.edges if e.src == node.id]
        used_by = [e.src for e in graph.edges if e.dst == node.id]
        body = [*self._links("Depends on", deps), *self._links("Depended on by", used_by)]
        return "\n".join([*head, *body])

    def _index(self, graph: GraphModel) -> str:
        lines = [
            f"# Code Knowledge Graph (v{graph.version})",
            "",
            f"- nodes: {len(graph.nodes)}",
            f"- edges: {len(graph.edges)}",
            "",
        ]
        for kind in NodeType:
            ids = [n.id for n in graph.nodes if n.type is kind]
            if ids:
                lines += self._links(f"{kind.value.capitalize()}s", ids)
        return "\n".join(lines)

    def _hot(self, graph: GraphModel, hot: list[str]) -> str:
        scores = self._fan_in(graph)
        lines = ["# Hot Nodes", "", "High fan-in nodes worth attention.", ""]
        body = [f"- {_link(n)} (fan-in {scores.get(n, 0)})" for n in hot] or ["- (none)"]
        return "\n".join([*lines, *body, ""])

    def _rank(self, graph: GraphModel) -> list[str]:
        scores = self._fan_in(graph)
        ranked = sorted(graph.node_ids(), key=lambda n: (-scores.get(n, 0), n))
        return [n for n in ranked if scores.get(n, 0) > 0][:_HOT_LIMIT]

    @staticmethod
    def _fan_in(graph: GraphModel) -> dict[str, int]:
        counts: dict[str, int] = {}
        for edge in graph.edges:
            counts[edge.dst] = counts.get(edge.dst, 0) + 1
        return counts

    @staticmethod
    def _links(title: str, ids: list[str]) -> list[str]:
        body = [f"- {_link(i)}" for i in ids] if ids else ["- (none)"]
        return [f"## {title}", *body, ""]
