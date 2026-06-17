"""Tests for :mod:`arch_agent.sdk.sdk` (all effects injected — offline)."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from arch_agent.infra.grphify_runner import GrphifyRunner
from arch_agent.infra.repo_loader import RepoLoader
from arch_agent.sdk import ArchAgentSDK
from arch_agent.shared.config import Config
from arch_agent.shared.gatekeeper import ApiGatekeeper, RateLimitConfig

_GRAPH = (
    '{"version":"1.00","nodes":[{"id":"a","type":"module","loc":400},'
    '{"id":"b","type":"module"}],"edges":[{"src":"b","dst":"a","kind":"import"}]}'
)


class FakeGraphify:
    def __call__(self, args: Sequence[str], cwd: Path) -> None:
        out = cwd / "graphify-out"
        out.mkdir(parents=True, exist_ok=True)
        (out / "graph.json").write_text(_GRAPH, encoding="utf-8")


def _client(prompt: str) -> str:
    return "do the refactor"


def _config(target: str) -> Config:
    return Config(
        setup={
            "version": "1.00",
            "target_repo": {"url": target},
            "model": {"name": "claude-sonnet-4-6"},
            "graph_analysis": {"oversized_loc": 100},
            "paths": {"artifacts": "artifacts", "obsidian": "obsidian", "reports": "reports"},
        },
        rate_limits={"version": "1.00"},
    )


def _sdk(root: Path, target: str) -> ArchAgentSDK:
    return ArchAgentSDK(
        _config(target),
        _client,
        root,
        grphify=GrphifyRunner(runner=FakeGraphify()),
        repo_loader=RepoLoader(runner=lambda args: None),
        gatekeeper=ApiGatekeeper(RateLimitConfig(requests_per_minute=0), sleep=lambda _: None),
    )


def test_build_graph(tmp_path: Path) -> None:
    graph = _sdk(tmp_path, "https://github.com/x/y").build_graph()
    assert graph.node_ids() == frozenset({"a", "b"})
    assert (tmp_path / "artifacts" / "graph.json").is_file()


def test_detect_smells_and_reverse_engineer(tmp_path: Path) -> None:
    sdk = _sdk(tmp_path, "https://github.com/x/y")
    graph = sdk.build_graph()
    smells = sdk.detect_smells(graph)
    assert any(f.smell == "oversized_module" for f in smells)  # node a loc 400 > 100
    assert "```mermaid" in sdk.reverse_engineer(graph)


def test_sync_obsidian(tmp_path: Path) -> None:
    sdk = _sdk(tmp_path, "https://github.com/x/y")
    vault = sdk.sync_obsidian(sdk.build_graph())
    assert (vault / "index.md").is_file()
    assert (vault / "hot.md").is_file()


def test_run_crew_produces_report(tmp_path: Path) -> None:
    sdk = _sdk(tmp_path, "https://github.com/x/y")
    report = sdk.run_crew(sdk.build_graph(), context="# index\n- node")
    assert report.repo == "https://github.com/x/y"
    assert "do the refactor" in report.to_markdown()  # the architect's summary


def test_measure_efficiency(tmp_path: Path) -> None:
    (tmp_path / "src.py").write_text("def f():\n    return 1\n" * 50, encoding="utf-8")
    index = tmp_path / "index.md"
    index.write_text("# index\n- a\n", encoding="utf-8")
    comparison = _sdk(tmp_path, "x").measure_efficiency(tmp_path, "task", [index])
    assert comparison.graph_guided.in_tokens < comparison.baseline.in_tokens


def test_dir_resolves_configured_paths(tmp_path: Path) -> None:
    assert _sdk(tmp_path, "x").dir("reports") == tmp_path / "reports"
