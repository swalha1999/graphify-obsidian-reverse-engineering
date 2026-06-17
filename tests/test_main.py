"""Offline end-to-end test for :mod:`arch_agent.__main__`."""

from __future__ import annotations

import json
import os
from collections.abc import Sequence
from pathlib import Path

import pytest

from arch_agent.__main__ import _load_dotenv, main
from arch_agent.infra.grphify_runner import GrphifyRunner
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


def _project(root: Path) -> None:
    target = root / "data" / "target"
    target.mkdir(parents=True)
    (target / "main.py").write_text("def buggy():\n    return 1 / 0\n", encoding="utf-8")
    config = root / "config"
    config.mkdir()
    (config / "setup.json").write_text(
        json.dumps(
            {
                "version": "1.00",
                "target_repo": {"url": str(target)},  # local path -> resolved, no clone
                "model": {"name": "claude-sonnet-4-6"},
                "graph_analysis": {"oversized_loc": 100},
                "token_efficiency": {"task": "find the bug"},
                "paths": {"artifacts": "artifacts", "obsidian": "obsidian", "reports": "reports"},
            }
        ),
        encoding="utf-8",
    )
    (config / "rate_limits.json").write_text('{"version": "1.00"}', encoding="utf-8")


def test_load_dotenv(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("# comment\nFOO=bar\nNOEQUALS\n", encoding="utf-8")
    os.environ.pop("FOO", None)
    _load_dotenv(env)
    assert os.environ["FOO"] == "bar"
    _load_dotenv(tmp_path / "missing.env")  # no-op, must not raise


def test_main_runs_pipeline_offline_and_writes_deliverables(tmp_path: Path) -> None:
    _project(tmp_path)
    code = main(
        tmp_path,
        client=lambda prompt: "split the god module",
        grphify=GrphifyRunner(runner=FakeGraphify()),
        gatekeeper=ApiGatekeeper(RateLimitConfig(requests_per_minute=0), sleep=lambda _: None),
    )
    assert code == 0
    # deliverables written to the configured folders
    assert (tmp_path / "artifacts" / "graph.json").is_file()
    assert (tmp_path / "obsidian" / "index.md").is_file()
    reports = tmp_path / "reports"
    assert (reports / "architecture.md").is_file()
    assert (reports / "recommendations.md").is_file()
    assert (reports / "recommendations.json").is_file()
    assert (reports / "token_efficiency.md").is_file()
    assert "Token-Efficiency Comparison" in (reports / "token_efficiency.md").read_text(
        encoding="utf-8"
    )


def test_main_rejects_incompatible_version(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _project(tmp_path)
    monkeypatch.setattr("arch_agent.__main__.is_compatible", lambda _: False)
    with pytest.raises(ValueError, match="incompatible"):
        main(
            tmp_path,
            client=lambda prompt: "x",
            grphify=GrphifyRunner(runner=FakeGraphify()),
            gatekeeper=ApiGatekeeper(RateLimitConfig(requests_per_minute=0), sleep=lambda _: None),
        )
