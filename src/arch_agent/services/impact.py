"""Impact analysis: blast radius and orphan components (original extension, FR-17).

Two analyses that go beyond the required smell set (PRD_graph_analysis.md §6,
FR-17), both pure deterministic functions of a :class:`GraphModel`:

* **Blast radius** — for a node ``n``, the set of nodes that *transitively depend
  on* ``n`` (reverse reachability over directed edges, ``src`` depends on ``dst``).
  This answers "if ``n`` breaks, what is impacted?" — a sharper risk signal than
  fan-in, because it counts indirect dependents too.
* **Orphan components** — nodes with neither dependents nor dependencies
  (fan-in and fan-out both zero): dead-ish code or missing wiring worth flagging.

Feeds research question RQ-8. See ``docs/EXTENSIONS.md``.
"""

from __future__ import annotations

from collections import defaultdict, deque

from arch_agent.services.models import GraphModel


class ImpactAnalyzer:
    """Compute blast radius and orphan components for a :class:`GraphModel`."""

    def __init__(self, graph: GraphModel) -> None:
        self._ids = graph.node_ids()
        # Reverse adjacency between known nodes: dependents[dst] = {src that depends on dst}.
        rev: dict[str, set[str]] = defaultdict(set)
        for edge in graph.edges:
            if edge.src in self._ids and edge.dst in self._ids:
                rev[edge.dst].add(edge.src)
        self._dependents = rev

    def blast_radius(self, node_id: str) -> frozenset[str]:
        """Return all nodes that transitively depend on ``node_id`` (excluding itself).

        Unknown ids yield an empty set. The node itself is never included, even in a cycle.
        """
        if node_id not in self._ids:
            return frozenset()
        seen: set[str] = set()
        queue: deque[str] = deque(self._dependents.get(node_id, set()))
        while queue:
            cur = queue.popleft()
            if cur == node_id or cur in seen:
                continue
            seen.add(cur)
            queue.extend(self._dependents.get(cur, set()))
        return frozenset(seen)

    def blast_radii(self) -> dict[str, int]:
        """Blast-radius *size* for every node, descending by impact then id."""
        sizes = {nid: len(self.blast_radius(nid)) for nid in self._ids}
        return dict(sorted(sizes.items(), key=lambda kv: (-kv[1], kv[0])))

    def orphans(self) -> frozenset[str]:
        """Nodes with no dependents and no dependencies (fan-in and fan-out both zero)."""
        # Every key in _dependents has >=1 src by construction, so any node that
        # appears as a key or in a value is connected; the rest are orphans.
        connected: set[str] = set(self._dependents)
        for srcs in self._dependents.values():
            connected.update(srcs)
        return frozenset(nid for nid in self._ids if nid not in connected)
