"""AgentCrew: LangGraph orchestration of the analyse->recommend workflow.

PRD_agent_workflow.md §2/§5, ADR-002. The roles are wired as a LangGraph
``StateGraph``: ``explore -> analyse -> recommend -> report``. Smells are detected
up front (no LLM); the agents then reason over the graph-derived context, never
raw source.
"""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from arch_agent.agents.roles import Analyst, Architect, Explorer, ModelClient, Reporter
from arch_agent.services.findings import Finding, SmellConfig
from arch_agent.services.models import GraphModel
from arch_agent.services.smells import SmellDetector
from arch_agent.shared.gatekeeper import ApiGatekeeper


class CrewState(TypedDict, total=False):
    """State threaded through the workflow nodes."""

    context: str
    findings: list[Finding]
    architecture: str
    analysis: str
    recommendations: str
    report: str


def _render_findings(findings: list[Finding]) -> str:
    """Render findings as a compact text summary for the Analyst."""
    if not findings:
        return "No architectural smells detected."
    lines = [f"- [{f.severity}] {f.smell} @ {f.node}: {f.rationale}" for f in findings]
    return "Detected smells:\n" + "\n".join(lines)


class AgentCrew:
    """Run the analyse->recommend agent workflow over a graph."""

    def __init__(
        self,
        gatekeeper: ApiGatekeeper,
        client: ModelClient,
        smell_config: SmellConfig | None = None,
    ) -> None:
        self._explorer = Explorer(gatekeeper, client)
        self._analyst = Analyst(gatekeeper, client)
        self._architect = Architect(gatekeeper, client)
        self._reporter = Reporter(gatekeeper, client)
        self._detector = SmellDetector(smell_config)
        self._app = self._build()

    def run(self, graph: GraphModel, context: str) -> CrewState:
        """Detect smells, then run the compiled workflow to completion."""
        findings = self._detector.detect(graph)
        initial: CrewState = {"context": context, "findings": findings}
        result: CrewState = self._app.invoke(initial)
        return result

    def _build(self) -> Any:
        graph = StateGraph(CrewState)
        graph.add_node("explore", self._explore)
        graph.add_node("analyse", self._analyse)
        graph.add_node("recommend", self._recommend)
        graph.add_node("report", self._report)
        graph.add_edge(START, "explore")
        graph.add_edge("explore", "analyse")
        graph.add_edge("analyse", "recommend")
        graph.add_edge("recommend", "report")
        graph.add_edge("report", END)
        return graph.compile()

    def _explore(self, state: CrewState) -> CrewState:
        return {"architecture": self._explorer.run(state["context"])}

    def _analyse(self, state: CrewState) -> CrewState:
        return {"analysis": self._analyst.run(_render_findings(state["findings"]))}

    def _recommend(self, state: CrewState) -> CrewState:
        return {"recommendations": self._architect.run(state["analysis"])}

    def _report(self, state: CrewState) -> CrewState:
        material = (
            f"Architecture:\n{state['architecture']}\n\n"
            f"Recommendations:\n{state['recommendations']}"
        )
        return {"report": self._reporter.run(material)}
