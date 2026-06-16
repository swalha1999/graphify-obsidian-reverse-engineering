"""Typed, validated graph data models.

The in-memory representation of a Grphify graph (PLAN.md §3.1,
PRD_graph_analysis.md §2.1). Models are frozen (immutable) and validate their
own invariants on construction. Parsing raw ``graph.json`` — including defensive
handling of missing/unknown fields — is the loader's job (TODO 1.4); these
models assume already-clean inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class NodeType(StrEnum):
    """Kind of code entity a node represents."""

    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"


class EdgeKind(StrEnum):
    """Kind of dependency an edge represents (``src`` depends on ``dst``)."""

    IMPORT = "import"
    CALL = "call"
    INHERIT = "inherit"


@dataclass(frozen=True)
class Node:
    """A module, class, or function in the graph."""

    id: str
    type: NodeType
    loc: int | None = None
    centrality: float | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("node id must be non-empty")
        if self.loc is not None and self.loc < 0:
            raise ValueError(f"node {self.id!r} has negative loc: {self.loc}")


@dataclass(frozen=True)
class Edge:
    """A directed dependency from ``src`` to ``dst``."""

    src: str
    dst: str
    kind: EdgeKind

    def __post_init__(self) -> None:
        if not self.src or not self.dst:
            raise ValueError("edge endpoints must be non-empty")


@dataclass(frozen=True)
class GraphModel:
    """A whole knowledge graph: a versioned set of nodes and edges."""

    version: str
    nodes: tuple[Node, ...]
    edges: tuple[Edge, ...]

    def __post_init__(self) -> None:
        if not self.version:
            raise ValueError("graph version must be non-empty")
        ids = [n.id for n in self.nodes]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate node ids in graph")

    def node_ids(self) -> frozenset[str]:
        """Return the set of node ids."""
        return frozenset(n.id for n in self.nodes)

    def dangling_edges(self) -> tuple[Edge, ...]:
        """Return edges whose endpoints are not both present as nodes."""
        ids = self.node_ids()
        return tuple(e for e in self.edges if e.src not in ids or e.dst not in ids)
