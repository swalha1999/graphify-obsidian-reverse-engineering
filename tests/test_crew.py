"""Tests for :mod:`arch_agent.agents.crew`."""

from __future__ import annotations

from pathlib import Path

from arch_agent.agents.crew import AgentCrew, _render_findings
from arch_agent.services.findings import Finding
from arch_agent.services.graph_loader import GraphLoader
from arch_agent.services.models import GraphModel
from arch_agent.shared.gatekeeper import ApiGatekeeper, RateLimitConfig

FIXTURE = Path(__file__).parent / "fixtures" / "graph.json"


class FakeClient:
    """Records prompts and returns a distinct reply per call."""

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def __call__(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return f"reply-{len(self.prompts)}"


def _gatekeeper() -> ApiGatekeeper:
    return ApiGatekeeper(RateLimitConfig(requests_per_minute=0), sleep=lambda _: None)


def test_render_findings_empty_and_nonempty() -> None:
    assert _render_findings([]) == "No architectural smells detected."
    finding = Finding("god_node", "mod.x", {"fan_in": 9}, "high", "split it", "too central")
    rendered = _render_findings([finding])
    assert "god_node @ mod.x" in rendered
    assert "[high]" in rendered


def test_crew_runs_to_completion_and_fills_state() -> None:
    client = FakeClient()
    crew = AgentCrew(_gatekeeper(), client)
    result = crew.run(GraphLoader().load(FIXTURE), context="INDEX + HOT notes")
    # all workflow stages produced output
    assert result["architecture"] == "reply-1"
    assert result["analysis"] == "reply-2"
    assert result["recommendations"] == "reply-3"
    assert result["report"] == "reply-4"
    assert len(client.prompts) == 4  # explore, analyse, recommend, report


def test_explore_sees_context_and_analyse_sees_findings() -> None:
    client = FakeClient()
    crew = AgentCrew(_gatekeeper(), client)
    crew.run(GraphLoader().load(FIXTURE), context="MY_CONTEXT")
    explore_prompt, analyse_prompt = client.prompts[0], client.prompts[1]
    assert "MY_CONTEXT" in explore_prompt
    assert "Explorer" in explore_prompt
    # the analyst reasons over detected smells (graph evidence), not raw code
    assert "god_node" in analyse_prompt
    assert "mod.core" in analyse_prompt


def test_crew_completes_on_empty_graph() -> None:
    client = FakeClient()
    crew = AgentCrew(_gatekeeper(), client)
    result = crew.run(GraphModel("1.00", (), ()), context="ctx")
    assert result["report"] == "reply-4"
    assert "No architectural smells detected." in client.prompts[1]
