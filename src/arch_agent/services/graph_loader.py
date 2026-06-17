"""Parse a Grphify ``graph.json`` into typed models — defensively.

The on-disk schema is treated as untrusted (PLAN.md §3.1, PRD_graph_analysis.md
§2.1/§6): missing optional fields default, unknown fields are ignored, and nodes
or edges with a missing required field or an unknown ``type``/``kind`` are
**skipped** rather than raising. A missing/blank ``version`` defaults to ``"0.0"``.
"""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path
from typing import Any, TypeVar

from arch_agent.services.graphify_adapter import is_graphify, normalize
from arch_agent.services.models import Edge, EdgeKind, GraphModel, Node, NodeType

_DEFAULT_VERSION = "0.0"
_E = TypeVar("_E", bound=StrEnum)


class GraphLoader:
    """Load and defensively parse ``graph.json`` into a :class:`GraphModel`."""

    def load(self, path: Path) -> GraphModel:
        """Read and parse the graph at ``path``."""
        return self.parse(json.loads(path.read_text(encoding="utf-8")))

    def parse(self, data: Any) -> GraphModel:
        """Build a :class:`GraphModel` from already-decoded JSON.

        Raises:
            ValueError: if ``data`` is not a JSON object.
        """
        if not isinstance(data, dict):
            raise ValueError("graph.json must be a JSON object")
        if is_graphify(data):
            data = normalize(data)  # graphify node-link -> PLAN schema
        version = self._str(data.get("version")) or _DEFAULT_VERSION
        nodes = self._nodes(data.get("nodes"))
        edges = self._edges(data.get("edges"))
        return GraphModel(version=version, nodes=nodes, edges=edges)

    def _nodes(self, raw: Any) -> tuple[Node, ...]:
        items = raw if isinstance(raw, list) else []
        return tuple(n for item in items if (n := self._node(item)) is not None)

    def _edges(self, raw: Any) -> tuple[Edge, ...]:
        items = raw if isinstance(raw, list) else []
        return tuple(e for item in items if (e := self._edge(item)) is not None)

    def _node(self, item: Any) -> Node | None:
        if not isinstance(item, dict):
            return None
        node_id = self._str(item.get("id"))
        node_type = self._enum(NodeType, item.get("type"))
        if node_id is None or node_type is None:
            return None
        return Node(
            id=node_id,
            type=node_type,
            loc=self._loc(item.get("loc")),
            centrality=self._num(item.get("centrality")),
        )

    def _edge(self, item: Any) -> Edge | None:
        if not isinstance(item, dict):
            return None
        src = self._str(item.get("src"))
        dst = self._str(item.get("dst"))
        kind = self._enum(EdgeKind, item.get("kind"))
        if src is None or dst is None or kind is None:
            return None
        return Edge(src=src, dst=dst, kind=kind)

    @staticmethod
    def _str(value: Any) -> str | None:
        return value if isinstance(value, str) and value else None

    @staticmethod
    def _enum(enum_cls: type[_E], value: Any) -> _E | None:
        try:
            return enum_cls(value)
        except ValueError:
            return None

    @staticmethod
    def _loc(value: Any) -> int | None:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            return None
        return value

    @staticmethod
    def _num(value: Any) -> float | None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        return float(value)
