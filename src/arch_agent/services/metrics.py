"""Structural metrics over a graph: fan-in/out, centrality, proximity.

Implements PRD_graph_analysis.md §3.1–§3.3. Every metric is a pure, deterministic
function of a :class:`GraphModel`. Cycle detection is a separate concern (TODO 2.2).

Edges are directed (``src`` depends on ``dst``); proximity treats them as
undirected. Adjacency is built only between *known* nodes, so a dangling edge
(an endpoint that is not a node) never bridges two real nodes.
"""

from __future__ import annotations

from collections import deque

from arch_agent.services.models import GraphModel


class MetricsCalculator:
    """Compute structural metrics for a :class:`GraphModel`."""

    def __init__(self, graph: GraphModel) -> None:
        self._graph = graph
        self._ids = graph.node_ids()

    def fan_in(self) -> dict[str, int]:
        """Count incoming edges per node (edges whose ``dst`` is the node)."""
        counts = dict.fromkeys(self._ids, 0)
        for edge in self._graph.edges:
            if edge.dst in counts:
                counts[edge.dst] += 1
        return counts

    def fan_out(self) -> dict[str, int]:
        """Count outgoing edges per node (edges whose ``src`` is the node)."""
        counts = dict.fromkeys(self._ids, 0)
        for edge in self._graph.edges:
            if edge.src in counts:
                counts[edge.src] += 1
        return counts

    def centrality(self) -> dict[str, float]:
        """Normalised degree centrality: ``(fan_in + fan_out) / (N - 1)`` in ``[0, 1]``."""
        n = len(self._graph.nodes)
        if n <= 1:
            return dict.fromkeys(self._ids, 0.0)
        fan_in, fan_out = self.fan_in(), self.fan_out()
        return {nid: (fan_in[nid] + fan_out[nid]) / (n - 1) for nid in self._ids}

    def proximity(self, seed: set[str]) -> dict[str, int]:
        """Shortest undirected hop distance from each node to the nearest ``seed`` node.

        Returns reachable nodes only (seed nodes are distance 0). Unknown seed ids
        are ignored.
        """
        adj = self._undirected_adj()
        dist: dict[str, int] = {}
        queue: deque[str] = deque()
        for node_id in seed:
            if node_id in self._ids:
                dist[node_id] = 0
                queue.append(node_id)
        while queue:
            cur = queue.popleft()
            for neighbour in adj[cur]:
                if neighbour not in dist:
                    dist[neighbour] = dist[cur] + 1
                    queue.append(neighbour)
        return dist

    def proximity_score(self, seed: set[str]) -> dict[str, float]:
        """Normalised proximity ``1 / (1 + dist)`` for every node; unreachable -> ``0.0``."""
        dist = self.proximity(seed)
        return {nid: 1.0 / (1 + dist[nid]) if nid in dist else 0.0 for nid in self._ids}

    def articulation_points(self) -> set[str]:
        """Nodes whose removal increases the number of connected components (SPOF basis)."""
        adj = self._undirected_adj()
        base = self._count_components(adj, None)
        return {nid for nid in self._ids if self._count_components(adj, nid) > base}

    @staticmethod
    def _count_components(adj: dict[str, set[str]], exclude: str | None) -> int:
        """Count connected components, optionally with one node removed."""
        seen: set[str] = set() if exclude is None else {exclude}
        count = 0
        for start in adj:
            if start in seen:
                continue
            count += 1
            stack = [start]
            seen.add(start)
            while stack:
                cur = stack.pop()
                for neighbour in adj[cur]:
                    if neighbour not in seen:
                        seen.add(neighbour)
                        stack.append(neighbour)
        return count

    def _undirected_adj(self) -> dict[str, set[str]]:
        """Undirected adjacency between known nodes (dangling edges excluded)."""
        adj: dict[str, set[str]] = {nid: set() for nid in self._ids}
        for edge in self._graph.edges:
            if edge.src in adj and edge.dst in adj:
                adj[edge.src].add(edge.dst)
                adj[edge.dst].add(edge.src)
        return adj
