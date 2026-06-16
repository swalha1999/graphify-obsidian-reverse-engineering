"""Tests for :mod:`arch_agent.services.verification`."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from pathlib import Path

import pytest

from arch_agent.infra.grphify_runner import GrphifyRunner
from arch_agent.services import verification as ver
from arch_agent.services.verification import Reverifier

_GRAPH_JSON = '{"version": "1.00", "nodes": [{"id": "a", "type": "module"}], "edges": []}'


class FakeGraphify:
    """Simulates `graphify extract` by writing a graph.json into cwd/graphify-out."""

    def __call__(self, args: Sequence[str], cwd: Path) -> None:
        out = cwd / "graphify-out"
        out.mkdir(parents=True, exist_ok=True)
        (out / "graph.json").write_text(_GRAPH_JSON, encoding="utf-8")


def _reverifier(tests_pass: bool, seen: list[Path] | None = None) -> Reverifier:
    def runner(repo: Path) -> bool:
        if seen is not None:
            seen.append(repo)
        return tests_pass

    return Reverifier(grphify=GrphifyRunner(runner=FakeGraphify()), test_runner=runner)


def test_reverify_regraphs_and_runs_tests(tmp_path: Path) -> None:
    seen: list[Path] = []
    repo = tmp_path / "repo"
    repo.mkdir()
    result = _reverifier(tests_pass=True, seen=seen).reverify(repo, tmp_path / "artifacts")
    assert result.tests_passed is True
    assert result.graph.node_ids() == frozenset({"a"})  # re-graphed and reloaded
    assert seen == [repo]  # tests ran against the repo


def test_reverify_reports_failing_tests(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    result = _reverifier(tests_pass=False).reverify(repo, tmp_path / "artifacts")
    assert result.tests_passed is False
    assert result.graph.node_ids() == frozenset({"a"})


@pytest.mark.parametrize(("code", "expected"), [(0, True), (1, False)])
def test_default_pytest_runner(monkeypatch: pytest.MonkeyPatch, code: int, expected: bool) -> None:
    class _Done:
        returncode = code

    def fake_run(cmd: list[str], **kwargs: object) -> _Done:
        return _Done()

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert ver._run_pytest(Path(".")) is expected
