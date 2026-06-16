"""Tests for :mod:`arch_agent.infra.grphify_runner`."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from pathlib import Path

import pytest

from arch_agent.infra import grphify_runner as gr
from arch_agent.infra.grphify_runner import GrphifyRunner


class FakeGraphify:
    """Simulates `graphify extract` by writing the named files into cwd/graphify-out."""

    def __init__(self, produced: Sequence[str]) -> None:
        self.produced = produced
        self.calls: list[tuple[list[str], Path]] = []

    def __call__(self, args: Sequence[str], cwd: Path) -> None:
        self.calls.append((list(args), cwd))
        out = cwd / "graphify-out"
        out.mkdir(parents=True, exist_ok=True)
        for name in self.produced:
            (out / name).write_text("{}" if name.endswith(".json") else "x")


def test_run_returns_graph_json_under_artifacts(tmp_path: Path) -> None:
    runner = FakeGraphify(["graph.json", "GRAPH_REPORT.md", "graph.html"])
    artifacts = tmp_path / "artifacts"
    result = GrphifyRunner(runner=runner).run(repo_path=tmp_path / "repo", artifacts_dir=artifacts)
    assert result == artifacts / "graph.json"
    assert result.is_file()
    assert (artifacts / "GRAPH_REPORT.md").is_file()
    assert (artifacts / "graph.html").is_file()


def test_run_invokes_extract_with_cwd(tmp_path: Path) -> None:
    runner = FakeGraphify(["graph.json"])
    artifacts = tmp_path / "artifacts"
    GrphifyRunner(runner=runner).run(repo_path=tmp_path / "repo", artifacts_dir=artifacts)
    args, cwd = runner.calls[0]
    assert args == ["extract", str(tmp_path / "repo")]
    assert cwd == artifacts


def test_collect_skips_absent_optional_files(tmp_path: Path) -> None:
    runner = FakeGraphify(["graph.json"])  # no GRAPH_REPORT.md / graph.html
    artifacts = tmp_path / "artifacts"
    GrphifyRunner(runner=runner).run(repo_path=tmp_path / "repo", artifacts_dir=artifacts)
    assert (artifacts / "graph.json").is_file()
    assert not (artifacts / "GRAPH_REPORT.md").exists()


def test_run_raises_when_no_graph_produced(tmp_path: Path) -> None:
    runner = FakeGraphify([])  # produces nothing
    with pytest.raises(FileNotFoundError, match="no graph.json"):
        GrphifyRunner(runner=runner).run(repo_path=tmp_path / "repo", artifacts_dir=tmp_path / "a")


def test_default_runner_is_real_graphify() -> None:
    assert GrphifyRunner()._run is gr._run_graphify


def test_run_graphify_invokes_subprocess(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def fake_run(cmd: list[str], **kwargs: object) -> None:
        captured["cmd"] = cmd
        captured["cwd"] = kwargs.get("cwd")

    monkeypatch.setattr(subprocess, "run", fake_run)
    gr._run_graphify(["extract", "x"], cwd=tmp_path)
    assert captured["cmd"] == ["graphify", "extract", "x"]
    assert captured["cwd"] == str(tmp_path)
