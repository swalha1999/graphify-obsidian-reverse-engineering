"""CLI: ``python -m arch_agent`` runs the full pipeline and writes the deliverables.

Loads ``.env``, validates the code + config versions at startup (NFR-9), then
drives the SDK end-to-end: build the graph (Grphify), write the Obsidian vault,
detect smells, reverse-engineer the diagrams, run the agent crew, and measure
token efficiency — writing ``artifacts/`` + ``obsidian/`` + ``reports/``.

External effects are injectable so the whole flow runs offline in tests; the
default (no injection) uses the real Grphify subprocess and Anthropic client and
therefore **spends tokens**.
"""

from __future__ import annotations

import os
from pathlib import Path

from arch_agent.agents.roles import ModelClient
from arch_agent.infra.grphify_runner import GrphifyRunner
from arch_agent.infra.model_client import AnthropicClient
from arch_agent.infra.repo_loader import RepoLoader
from arch_agent.sdk import ArchAgentSDK
from arch_agent.shared.config import EXPECTED_VERSION, load_config
from arch_agent.shared.gatekeeper import ApiGatekeeper
from arch_agent.version import __version__, is_compatible


def _load_dotenv(path: Path) -> None:
    """Populate ``os.environ`` from a ``.env`` file (without overriding existing)."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main(
    root: Path | None = None,
    *,
    client: ModelClient | None = None,
    grphify: GrphifyRunner | None = None,
    repo_loader: RepoLoader | None = None,
    gatekeeper: ApiGatekeeper | None = None,
) -> int:
    """Run the pipeline; return a process exit code."""
    base = root or Path.cwd()
    _load_dotenv(base / ".env")
    if not is_compatible(EXPECTED_VERSION):
        raise ValueError(f"code version {__version__} incompatible with config {EXPECTED_VERSION}")
    config = load_config(base / "config")
    model_client = client or AnthropicClient(config.model, config.max_tokens)
    sdk = ArchAgentSDK(
        config, model_client, base, grphify=grphify, repo_loader=repo_loader, gatekeeper=gatekeeper
    )
    print(f"ArchAgent v{__version__} | target {config.target_repo} | model {config.model}")

    graph = sdk.build_graph()
    print(f"graph: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
    vault = sdk.sync_obsidian(graph)
    findings = sdk.detect_smells(graph)
    print(f"smells: {len(findings)}")

    reports = sdk.dir("reports")
    _write(reports / "architecture.md", sdk.reverse_engineer(graph))
    context = "\n\n".join(
        (vault / name).read_text(encoding="utf-8") for name in ("index.md", "hot.md")
    )
    report = sdk.run_crew(graph, context)
    _write(reports / "recommendations.md", report.to_markdown())
    _write(reports / "recommendations.json", report.to_json())

    task = str(config.setup.get("token_efficiency", {}).get("task", "find_root_cause_and_fix"))
    comparison = sdk.measure_efficiency(
        sdk.target_dir, task, [vault / "index.md", vault / "hot.md"]
    )
    _write(reports / "token_efficiency.md", comparison.to_markdown())
    print(f"token savings: {comparison.savings_pct()}% -> {reports}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
