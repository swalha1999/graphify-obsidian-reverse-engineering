"""Tests for :mod:`arch_agent.agents.guards` and the FR 3.5 enforcement in agents."""

from __future__ import annotations

from pathlib import Path

import pytest

from arch_agent.agents.crew import AgentCrew
from arch_agent.agents.guards import (
    RawSourceError,
    assert_graph_only,
    count_source_signals,
    looks_like_raw_source,
)
from arch_agent.agents.roles import Explorer
from arch_agent.services.graph_loader import GraphLoader
from arch_agent.services.reverse_engineer import ReverseEngineer
from arch_agent.shared.gatekeeper import ApiGatekeeper, RateLimitConfig

FIXTURE = Path(__file__).parent / "fixtures" / "graph.json"

_RAW_SOURCE = """\
import os
from sys import argv


def main(arg):
    return arg


class Service:
    def run(self):
        return 1
"""

_GRAPH_CONTEXT = """\
# index.md

- [[mod.core|mod.core]] (fan-in 6)
- [[mod.api|mod.api]]

Detected smells:
- [high] god_node @ mod.core: too central
"""


def _gatekeeper() -> ApiGatekeeper:
    return ApiGatekeeper(RateLimitConfig(requests_per_minute=0), sleep=lambda _: None)


def test_detects_raw_source() -> None:
    assert count_source_signals(_RAW_SOURCE) >= 3
    assert looks_like_raw_source(_RAW_SOURCE)


def test_graph_artifacts_are_not_flagged() -> None:
    assert count_source_signals(_GRAPH_CONTEXT) == 0
    assert not looks_like_raw_source(_GRAPH_CONTEXT)


def test_mermaid_class_diagram_not_flagged() -> None:
    class_map = ReverseEngineer().class_map(GraphLoader().load(FIXTURE))
    assert not looks_like_raw_source(class_map)  # "class Foo" without ':' is fine


def test_assert_graph_only_raises_on_source() -> None:
    with pytest.raises(RawSourceError, match="raw-source signals"):
        assert_graph_only(_RAW_SOURCE)


def test_assert_graph_only_passes_artifacts() -> None:
    assert_graph_only(_GRAPH_CONTEXT)  # does not raise


def test_agent_run_rejects_raw_source_before_calling_model() -> None:
    called = {"n": 0}

    def client(prompt: str) -> str:
        called["n"] += 1
        return "x"

    explorer = Explorer(_gatekeeper(), client)
    with pytest.raises(RawSourceError):
        explorer.run(_RAW_SOURCE)
    assert called["n"] == 0  # model never invoked


def test_crew_prompts_are_all_graph_only() -> None:
    prompts: list[str] = []

    def client(prompt: str) -> str:
        prompts.append(prompt)
        return "ok"

    AgentCrew(_gatekeeper(), client).run(GraphLoader().load(FIXTURE), context=_GRAPH_CONTEXT)
    assert prompts  # the crew ran
    assert all(not looks_like_raw_source(p) for p in prompts)  # no whole-file dumps
