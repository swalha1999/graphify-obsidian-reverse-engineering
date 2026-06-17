"""Tests for the baseline run in :mod:`arch_agent.services.study`."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from arch_agent.services.study import estimate_tokens, run_baseline
from arch_agent.shared.gatekeeper import ApiGatekeeper, RateLimitConfig


class FakeClient:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def __call__(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return "the root cause is X; fix Y"


def _gatekeeper() -> ApiGatekeeper:
    return ApiGatekeeper(RateLimitConfig(requests_per_minute=0), sleep=lambda _: None)


def _clock(values: list[float]) -> Callable[[], float]:
    it = iter(values)
    return lambda: next(it)


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "pkg").mkdir(parents=True)
    (repo / "main.py").write_text("def buggy():\n    return 1 / 0\n", encoding="utf-8")
    (repo / "pkg" / "util.py").write_text("x = 1\n", encoding="utf-8")
    return repo


def test_estimate_tokens() -> None:
    assert estimate_tokens("") == 1  # floor of 1
    assert estimate_tokens("a" * 40) == 10


def test_baseline_dumps_all_py_files_and_records_metrics(tmp_path: Path) -> None:
    client = FakeClient()
    record = run_baseline(
        _repo(tmp_path), "find the bug", client, _gatekeeper(), clock=_clock([0.0, 3.0])
    )
    assert record.files_read == 2  # main.py + pkg/util.py
    assert record.iterations == 1
    assert record.in_tokens > record.out_tokens  # whole-file dump dominates input
    assert record.time_to_root_cause_s == 3.0
    assert record.root_cause_found is True
    # the naive control really does put raw source in the prompt
    assert "def buggy():" in client.prompts[0]
    assert "RAW SOURCE (2 files)" in client.prompts[0]


def test_baseline_iterations(tmp_path: Path) -> None:
    client = FakeClient()
    record = run_baseline(
        _repo(tmp_path), "task", client, _gatekeeper(), iterations=3, clock=_clock([0.0, 1.0])
    )
    assert record.iterations == 3
    assert len(client.prompts) == 3


def test_baseline_outcome_flags_passthrough(tmp_path: Path) -> None:
    record = run_baseline(
        _repo(tmp_path),
        "task",
        FakeClient(),
        _gatekeeper(),
        clock=_clock([0.0, 1.0]),
        root_cause_found=False,
        tests_green=False,
    )
    assert record.root_cause_found is False
    assert record.tests_green is False
