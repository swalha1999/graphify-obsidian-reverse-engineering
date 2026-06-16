"""Run independent metric computations concurrently (PRD NFR-8, TODO 2.5).

Every task is a **pure read** of a frozen :class:`GraphModel` with no shared
mutable state, so they are inherently thread-safe and a parallel run yields
exactly the same result as a sequential one. A thread pool is used (simple, no
pickling); the same shape works with a process pool for CPU-bound parallelism.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from arch_agent.services.cycles import find_cycles, find_self_loops
from arch_agent.services.metrics import MetricsCalculator
from arch_agent.services.models import GraphModel


@dataclass(frozen=True)
class MetricsResult:
    """The bundle of independent metrics for a graph."""

    fan_in: dict[str, int]
    fan_out: dict[str, int]
    centrality: dict[str, float]
    articulation_points: frozenset[str]
    cycles: tuple[tuple[str, ...], ...]
    self_loops: tuple[str, ...]


def compute_metrics(graph: GraphModel, max_workers: int | None = None) -> MetricsResult:
    """Compute the independent metrics for ``graph`` concurrently."""
    metrics = MetricsCalculator(graph)
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        fan_in = pool.submit(metrics.fan_in)
        fan_out = pool.submit(metrics.fan_out)
        centrality = pool.submit(metrics.centrality)
        articulation = pool.submit(metrics.articulation_points)
        cycles = pool.submit(find_cycles, graph)
        self_loops = pool.submit(find_self_loops, graph)
        return MetricsResult(
            fan_in=fan_in.result(),
            fan_out=fan_out.result(),
            centrality=centrality.result(),
            articulation_points=frozenset(articulation.result()),
            cycles=tuple(tuple(c) for c in cycles.result()),
            self_loops=tuple(self_loops.result()),
        )
