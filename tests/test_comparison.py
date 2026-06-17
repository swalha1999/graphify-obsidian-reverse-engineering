"""Tests for :mod:`arch_agent.services.comparison`."""

from __future__ import annotations

import json

from arch_agent.services.comparison import build_comparison
from arch_agent.services.efficiency import RunRecord


def _rec(
    in_tokens: int,
    out_tokens: int,
    *,
    files_read: int = 0,
    units_read: int = 0,
    iterations: int = 1,
    ttrc: float | None = 1.0,
    root_cause_found: bool = True,
    tests_green: bool = True,
) -> RunRecord:
    return RunRecord(
        in_tokens,
        out_tokens,
        0.0,
        files_read,
        units_read,
        iterations,
        ttrc,
        root_cause_found,
        tests_green,
    )


def test_savings_pct_and_verdict_meets_target() -> None:
    cmp = build_comparison("t", baseline=_rec(900, 100), graph_guided=_rec(180, 20))
    assert cmp.savings_pct() == 80.0  # (1000-200)/1000
    assert "meets the >=40% target" in cmp.verdict()


def test_savings_positive_but_below_target() -> None:
    cmp = build_comparison("t", baseline=_rec(80, 20), graph_guided=_rec(64, 16))
    assert cmp.savings_pct() == 20.0
    assert "below the 40% target" in cmp.verdict()


def test_no_savings_when_guided_heavier() -> None:
    cmp = build_comparison("t", baseline=_rec(50, 50), graph_guided=_rec(100, 50))
    assert cmp.savings_pct() == -50.0
    assert "no token savings" in cmp.verdict()


def test_zero_baseline_guarded() -> None:
    assert build_comparison("t", baseline=_rec(0, 0), graph_guided=_rec(0, 0)).savings_pct() == 0.0


def test_to_dict_structure() -> None:
    cmp = build_comparison("find-bug", baseline=_rec(900, 100), graph_guided=_rec(180, 20))
    data = json.loads(json.dumps(cmp.to_dict()))  # must be JSON-serialisable
    assert data["task"] == "find-bug"
    assert data["savings_pct"] == 80.0
    assert data["baseline"]["in_tokens"] == 900
    assert data["graph_guided"]["in_tokens"] == 180


def test_to_markdown_covers_all_metrics() -> None:
    cmp = build_comparison(
        "find-bug",
        baseline=_rec(900, 100, files_read=12, units_read=400, iterations=5, ttrc=600.0),
        graph_guided=_rec(180, 20, files_read=2, units_read=30, iterations=2, ttrc=120.0),
    )
    md = cmp.to_markdown()
    assert "# Token-Efficiency Comparison — find-bug" in md
    for metric in [
        "Input tokens",
        "Total tokens",
        "Files read",
        "Iterations",
        "Time to root cause",
    ]:
        assert metric in md
    assert "| Total tokens | 1000 | 200 |" in md
    assert "Token savings (graph-guided vs baseline): 80.0%" in md


def test_markdown_time_na_when_unmeasured() -> None:
    cmp = build_comparison("t", baseline=_rec(10, 0, ttrc=None), graph_guided=_rec(5, 0, ttrc=None))
    assert "n/a" in cmp.to_markdown()
