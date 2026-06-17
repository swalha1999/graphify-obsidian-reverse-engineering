"""ArchAgentSDK — the single entry point every operation goes through (PRD FR-15).

Thin façade that wires the existing services/agents/infra together using a
:class:`Config`. External effects (repo clone, Grphify subprocess, LLM calls) are
injected, so the whole pipeline is exercisable offline in tests.
"""

from __future__ import annotations

from pathlib import Path

from arch_agent.agents.crew import AgentCrew, CrewState
from arch_agent.agents.roles import ModelClient
from arch_agent.infra.grphify_runner import GrphifyRunner
from arch_agent.infra.repo_loader import RepoLoader
from arch_agent.services.comparison import EfficiencyComparison, build_comparison
from arch_agent.services.findings import Finding, SmellConfig
from arch_agent.services.graph_loader import GraphLoader
from arch_agent.services.models import GraphModel
from arch_agent.services.obsidian_sync import ObsidianSync
from arch_agent.services.recommendation import RecommendationReport, build_report
from arch_agent.services.reverse_engineer import ReverseEngineer
from arch_agent.services.smells import SmellDetector
from arch_agent.services.study import run_baseline, run_graph_guided
from arch_agent.shared.config import Config
from arch_agent.shared.gatekeeper import ApiGatekeeper, RateLimitConfig


class ArchAgentSDK:
    """Public façade over the graph pipeline, analysis, agent crew, and study."""

    def __init__(
        self,
        config: Config,
        client: ModelClient,
        root: Path,
        *,
        grphify: GrphifyRunner | None = None,
        repo_loader: RepoLoader | None = None,
        gatekeeper: ApiGatekeeper | None = None,
    ) -> None:
        self._config = config
        self._client = client
        self._root = root
        self._grphify = grphify or GrphifyRunner()
        self._repo_loader = repo_loader or RepoLoader()
        self._gatekeeper = gatekeeper or ApiGatekeeper(
            RateLimitConfig.from_dict(config.rate_limits)
        )
        self._smell_config = SmellConfig.from_dict(config.graph_analysis)

    def dir(self, name: str) -> Path:
        """Resolve a configured output directory under the project root."""
        return self._root / str(self._config.paths.get(name, name))

    @property
    def target_dir(self) -> Path:
        return self._root / "data" / "target"

    def build_graph(self, repo: str | None = None) -> GraphModel:
        """Load the target repo, run Grphify, and parse ``graph.json``."""
        local = self._repo_loader.load(repo or self._config.target_repo, self.target_dir)
        graph_path = self._grphify.run(local, self.dir("artifacts"))
        return GraphLoader().load(graph_path)

    def detect_smells(self, graph: GraphModel) -> list[Finding]:
        return SmellDetector(self._smell_config).detect(graph)

    def reverse_engineer(self, graph: GraphModel) -> str:
        return ReverseEngineer().render(graph)

    def sync_obsidian(self, graph: GraphModel) -> Path:
        return ObsidianSync().write(graph, self.dir("obsidian"))

    def run_crew(self, graph: GraphModel, context: str) -> RecommendationReport:
        state: CrewState = AgentCrew(self._gatekeeper, self._client, self._smell_config).run(
            graph, context
        )
        return build_report(
            self.detect_smells(graph),
            self._config.target_repo,
            summary=state.get("recommendations", ""),
        )

    def measure_efficiency(
        self, repo_path: Path, task: str, artifacts: list[Path]
    ) -> EfficiencyComparison:
        baseline = run_baseline(repo_path, task, self._client, self._gatekeeper)
        guided = run_graph_guided(artifacts, task, self._client, self._gatekeeper)
        return build_comparison(task, baseline, guided)
