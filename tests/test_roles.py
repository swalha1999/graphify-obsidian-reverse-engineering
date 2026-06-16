"""Tests for :mod:`arch_agent.agents.roles`."""

from __future__ import annotations

import pytest

from arch_agent.agents.roles import (
    Agent,
    Analyst,
    Architect,
    Explorer,
    Refactor,
    Reporter,
    build_crew,
)
from arch_agent.shared.gatekeeper import ApiGatekeeper, RateLimitConfig


def _gatekeeper() -> ApiGatekeeper:
    # rpm=0 disables rate limiting so tests do not sleep
    return ApiGatekeeper(RateLimitConfig(requests_per_minute=0), sleep=lambda _: None)


class _RecordingClient:
    """Captures the prompt and returns a canned (padded) completion."""

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def __call__(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return "  answer  "


def test_base_agent_is_abstract() -> None:
    with pytest.raises(TypeError):
        Agent(_gatekeeper(), lambda p: p)  # type: ignore[abstract]


def test_build_crew_is_five_distinct_roles_in_order() -> None:
    crew = build_crew(_gatekeeper(), lambda p: p)
    assert [a.name() for a in crew] == ["Explorer", "Analyst", "Architect", "Refactor", "Reporter"]
    assert all(a.responsibility() for a in crew)  # each non-empty
    assert len({a.name() for a in crew}) == 5


def test_run_routes_through_gatekeeper_and_parses() -> None:
    client = _RecordingClient()
    explorer = Explorer(_gatekeeper(), client)
    result = explorer.run("INDEX+HOT")
    assert result == "answer"  # parse() strips whitespace
    assert len(client.prompts) == 1
    prompt = client.prompts[0]
    assert prompt.startswith("You are the Explorer agent.")
    assert "index.md" in prompt
    assert "INDEX+HOT" in prompt  # context embedded


@pytest.mark.parametrize(
    ("cls", "expected"),
    [
        (Explorer, "Explorer"),
        (Analyst, "Analyst"),
        (Architect, "Architect"),
        (Refactor, "Refactor"),
        (Reporter, "Reporter"),
    ],
)
def test_each_role_name_and_responsibility(cls: type, expected: str) -> None:
    agent = cls(_gatekeeper(), lambda p: p)
    assert agent.name() == expected
    assert len(agent.responsibility()) > 0


def test_every_agent_runs_via_crew() -> None:
    client = _RecordingClient()
    crew = build_crew(_gatekeeper(), client)
    for agent in crew:
        assert agent.run("ctx") == "answer"
    assert len(client.prompts) == 5  # all five routed a call
