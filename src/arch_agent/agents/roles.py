"""Agent roles for the crew (PRD_agent_workflow.md §4).

Five single-responsibility agents share one base, :class:`Agent`. The base owns
the cross-cutting work — assemble the prompt (role instruction + curated
context), route the model call through the :class:`ApiGatekeeper`, and parse the
completion. Each subclass declares only the one responsibility it owns; none
reads raw source (FR 3.5) — they reason over the graph artifacts.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

from arch_agent.shared.gatekeeper import ApiGatekeeper

ModelClient = Callable[[str], str]


class Agent(ABC):
    """Base agent: prompt assembly + gatekept model call + parsing."""

    def __init__(self, gatekeeper: ApiGatekeeper, client: ModelClient) -> None:
        self._gatekeeper = gatekeeper
        self._client = client

    @abstractmethod
    def name(self) -> str:
        """The agent's display name."""

    @abstractmethod
    def responsibility(self) -> str:
        """The single responsibility this agent owns (its system instruction)."""

    def build_prompt(self, context: str) -> str:
        """Assemble the role instruction with the curated context."""
        return f"You are the {self.name()} agent. {self.responsibility()}\n\n---\n{context}"

    def parse(self, raw: str) -> str:
        """Post-process the model completion."""
        return raw.strip()

    def run(self, context: str) -> str:
        """Build the prompt, call the model via the gatekeeper, and parse the result."""
        prompt = self.build_prompt(context)
        return self.parse(self._gatekeeper.execute(self._client, prompt))


class Explorer(Agent):
    """Understand the system."""

    def name(self) -> str:
        return "Explorer"

    def responsibility(self) -> str:
        return (
            "Summarise the system architecture using only the curated index.md and "
            "hot.md notes — never raw source files."
        )


class Analyst(Agent):
    """Find structural risk."""

    def name(self) -> str:
        return "Analyst"

    def responsibility(self) -> str:
        return (
            "Identify structural risk: rank the architectural smells with evidence "
            "drawn from the graph metrics."
        )


class Architect(Agent):
    """Decide what to change."""

    def name(self) -> str:
        return "Architect"

    def responsibility(self) -> str:
        return "Decide what to change: produce ordered, justified refactoring recommendations."


class Refactor(Agent):
    """Execute one change safely."""

    def name(self) -> str:
        return "Refactor"

    def responsibility(self) -> str:
        return (
            "Execute one change safely: produce a minimal patch for the top "
            "recommendation, touching only what is needed."
        )


class Reporter(Agent):
    """Communicate results."""

    def name(self) -> str:
        return "Reporter"

    def responsibility(self) -> str:
        return "Communicate results: write the before/after architecture and token report."


def build_crew(gatekeeper: ApiGatekeeper, client: ModelClient) -> list[Agent]:
    """Construct the five agents in workflow order."""
    roles: list[type[Agent]] = [Explorer, Analyst, Architect, Refactor, Reporter]
    return [role(gatekeeper, client) for role in roles]
