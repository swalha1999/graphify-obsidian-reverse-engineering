"""Tests for :mod:`arch_agent.services.parallel`."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from arch_agent.services.cycles import find_cycles, find_self_loops
from arch_agent.services.graph_loader import GraphLoader
from arch_agent.services.metrics import MetricsCalculator
from arch_agent.services.models import GraphModel
from arch_agent.services.parallel import MetricsResult, compute_metrics

FIXTURE = Path(__file__).parent / "fixtures" / "graph.json"


def _fixture() -> GraphModel:
    return GraphLoader().load(FIXTURE)


def _sequential(graph: GraphModel) -> MetricsResult:
    m = MetricsCalculator(graph)
    return MetricsResult(
        fan_in=m.fan_in(),
        fan_out=m.fan_out(),
        centrality=m.centrality(),
        articulation_points=frozenset(m.articulation_points()),
        cycles=tuple(tuple(c) for c in find_cycles(graph)),
        self_loops=tuple(find_self_loops(graph)),
    )


def test_parallel_matches_sequential() -> None:
    graph = _fixture()
    assert compute_metrics(graph) == _sequential(graph)


def test_single_worker_matches() -> None:
    graph = _fixture()
    assert compute_metrics(graph, max_workers=1) == _sequential(graph)


def test_empty_graph() -> None:
    result = compute_metrics(GraphModel("1.00", (), ()))
    assert result.fan_in == {}
    assert result.cycles == ()
    assert result.articulation_points == frozenset()


def test_thread_safe_under_concurrent_callers() -> None:
    graph = _fixture()
    expected = _sequential(graph)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = [pool.submit(compute_metrics, graph) for _ in range(32)]
        assert all(r.result() == expected for r in results)


def test_known_fixture_values() -> None:
    result = compute_metrics(_fixture())
    assert result.fan_in["mod.core"] == 6
    assert result.cycles == (("mod.a", "mod.b", "mod.c"),)
    assert result.self_loops == ()
