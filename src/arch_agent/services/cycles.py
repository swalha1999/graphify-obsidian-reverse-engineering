"""Cycle detection via strongly connected components (PRD_graph_analysis.md §3.4).

A dependency cycle is an SCC of size > 1, found with Tarjan's algorithm in O(N+E).
Self-loops (``src == dst``) are reported separately. Dangling edges (an endpoint
that is not a node) are ignored. Results are sorted for determinism.

Tarjan is implemented **iteratively** (explicit work stack) so deep graphs cannot
overflow Python's recursion limit.
"""

from __future__ import annotations

from arch_agent.services.models import GraphModel


def find_self_loops(graph: GraphModel) -> list[str]:
    """Return node ids that have an edge to themselves."""
    ids = graph.node_ids()
    return sorted({e.src for e in graph.edges if e.src == e.dst and e.src in ids})


def find_cycles(graph: GraphModel) -> list[list[str]]:
    """Return dependency cycles (SCCs of size > 1); each cycle sorted, list sorted."""
    cycles = [sorted(component) for component in _sccs(graph) if len(component) > 1]
    return sorted(cycles, key=lambda c: c[0])


def _sccs(graph: GraphModel) -> list[list[str]]:
    """All strongly connected components (Tarjan, iterative)."""
    ids = graph.node_ids()
    adj: dict[str, list[str]] = {nid: [] for nid in ids}
    for edge in graph.edges:
        if edge.src in adj and edge.dst in adj and edge.src != edge.dst:
            adj[edge.src].append(edge.dst)

    index: dict[str, int] = {}
    low: dict[str, int] = {}
    on_stack: set[str] = set()
    stack: list[str] = []
    result: list[list[str]] = []
    counter = 0

    for root in ids:
        if root in index:
            continue
        work: list[tuple[str, int]] = [(root, 0)]
        while work:
            node, pos = work[-1]
            if pos == 0:
                index[node] = low[node] = counter
                counter += 1
                stack.append(node)
                on_stack.add(node)
            recursed = False
            neighbours = adj[node]
            while pos < len(neighbours):
                nb = neighbours[pos]
                pos += 1
                if nb not in index:
                    work[-1] = (node, pos)
                    work.append((nb, 0))
                    recursed = True
                    break
                if nb in on_stack:
                    low[node] = min(low[node], index[nb])
            if recursed:
                continue
            if low[node] == index[node]:
                result.append(_pop_component(stack, on_stack, node))
            work.pop()
            if work:
                parent = work[-1][0]
                low[parent] = min(low[parent], low[node])
    return result


def _pop_component(stack: list[str], on_stack: set[str], root: str) -> list[str]:
    """Pop the SCC rooted at ``root`` off the Tarjan stack."""
    component: list[str] = []
    while True:
        node = stack.pop()
        on_stack.discard(node)
        component.append(node)
        if node == root:
            return component
