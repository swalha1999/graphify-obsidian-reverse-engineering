"""Tests for the graph-guided run in :mod:`arch_agent.services.study`."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from arch_agent.services.study import run_baseline, run_graph_guided
from arch_agent.shared.gatekeeper import ApiGatekeeper, RateLimitConfig


class FakeClient:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def __call__(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return "root cause: division by zero"


def _gatekeeper() -> ApiGatekeeper:
    return ApiGatekeeper(RateLimitConfig(requests_per_minute=0), sleep=lambda _: None)


def _clock(values: list[float]) -> Callable[[], float]:
    it = iter(values)
    return lambda: next(it)


def _artifacts(tmp_path: Path) -> list[Path]:
    index = tmp_path / "index.md"
    hot = tmp_path / "hot.md"
    index.write_text("# index\n- [[main|main]]\n", encoding="utf-8")
    hot.write_text("# hot\n- main (fan-in 3)\n", encoding="utf-8")
    return [index, hot]


def test_graph_guided_feeds_only_artifacts_and_records_metrics(tmp_path: Path) -> None:
    client = FakeClient()
    record = run_graph_guided(
        _artifacts(tmp_path), "find the bug", client, _gatekeeper(), clock=_clock([0.0, 2.0])
    )
    assert record.files_read == 2  # index.md + hot.md, not source files
    assert record.iterations == 1
    assert record.time_to_root_cause_s == 2.0
    prompt = client.prompts[0]
    assert "GRAPH ARTIFACTS (2 files)" in prompt
    assert "fan-in 3" in prompt  # curated context
    assert "def " not in prompt  # no raw source


def test_graph_guided_uses_far_fewer_tokens_than_baseline(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    # a chunky source file -> heavy baseline
    (repo / "main.py").write_text("def f():\n    return 1\n" * 200, encoding="utf-8")

    baseline = run_baseline(repo, "task", FakeClient(), _gatekeeper(), clock=_clock([0.0, 1.0]))
    guided = run_graph_guided(
        _artifacts(tmp_path), "task", FakeClient(), _gatekeeper(), clock=_clock([0.0, 1.0])
    )
    assert guided.in_tokens < baseline.in_tokens  # the core token-efficiency thesis


def test_graph_guided_iterations(tmp_path: Path) -> None:
    client = FakeClient()
    record = run_graph_guided(
        _artifacts(tmp_path), "task", client, _gatekeeper(), iterations=2, clock=_clock([0.0, 1.0])
    )
    assert record.iterations == 2
    assert len(client.prompts) == 2
