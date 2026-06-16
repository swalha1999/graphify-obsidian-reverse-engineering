"""Tests for :mod:`arch_agent.infra.repo_loader`."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from pathlib import Path

import pytest

from arch_agent.infra import repo_loader as rl
from arch_agent.infra.repo_loader import RepoLoader, is_url


class FakeRunner:
    """Records git calls instead of executing them."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def __call__(self, args: Sequence[str]) -> None:
        self.calls.append(list(args))


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("https://github.com/a/b", True),
        ("http://example.com/x", True),
        ("git@github.com:a/b.git", True),
        ("ssh://git@host/a/b", True),
        ("/home/user/repo", False),
        ("./relative/repo", False),
    ],
)
def test_is_url(source: str, expected: bool) -> None:
    assert is_url(source) is expected


def test_load_local_path_resolves(tmp_path: Path) -> None:
    loader = RepoLoader(runner=FakeRunner())
    result = loader.load(str(tmp_path), dest=tmp_path / "unused")
    assert result == tmp_path.resolve()


def test_load_local_path_missing_raises(tmp_path: Path) -> None:
    loader = RepoLoader(runner=FakeRunner())
    with pytest.raises(FileNotFoundError, match="local repo path not found"):
        loader.load(str(tmp_path / "nope"), dest=tmp_path / "unused")


def test_load_url_clones(tmp_path: Path) -> None:
    runner = FakeRunner()
    dest = tmp_path / "clone"
    result = RepoLoader(runner=runner).load("https://github.com/a/b", dest=dest)
    assert result == dest
    assert runner.calls == [["clone", "--depth", "1", "https://github.com/a/b", str(dest)]]


def test_load_url_with_ref_checks_out(tmp_path: Path) -> None:
    runner = FakeRunner()
    dest = tmp_path / "clone"
    RepoLoader(runner=runner).load("https://github.com/a/b", dest=dest, ref="dev")
    assert runner.calls[-1] == ["-C", str(dest), "checkout", "dev"]


def test_clone_replaces_existing_dest(tmp_path: Path) -> None:
    dest = tmp_path / "clone"
    dest.mkdir()
    (dest / "stale.txt").write_text("old")
    RepoLoader(runner=FakeRunner()).load("https://github.com/a/b", dest=dest)
    assert not (dest / "stale.txt").exists()


def test_default_runner_is_real_git() -> None:
    assert RepoLoader()._run is rl._run_git


def test_run_git_invokes_subprocess(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_run(cmd: list[str], **kwargs: object) -> None:
        captured["cmd"] = cmd

    monkeypatch.setattr(subprocess, "run", fake_run)
    rl._run_git(["clone", "x"])
    assert captured["cmd"] == ["git", "clone", "x"]
