"""Tests for :mod:`arch_agent.agents.loop`."""

from __future__ import annotations

from collections.abc import Callable

from arch_agent.agents.loop import LoopState, StopConfig, StopCriterion


def _crit(**kw: float | int) -> StopCriterion:
    return StopCriterion(StopConfig(**kw))  # type: ignore[arg-type]


def _recording_step(value: float) -> tuple[Callable[[int], float], list[int]]:
    calls: list[int] = []

    def step(iteration: int) -> float:
        calls.append(iteration)
        return value

    return step, calls


def test_stop_on_max_iterations() -> None:
    stop, reason = _crit(max_iterations=3).should_stop(LoopState(3, 1.0, 0))
    assert stop and reason == "max_iterations"


def test_stop_on_budget() -> None:
    stop, reason = _crit(token_budget=100).should_stop(LoopState(0, 1.0, 100))
    assert stop and reason == "budget_exceeded"


def test_stop_on_no_improvement() -> None:
    stop, reason = _crit(min_metric_improvement=0.05).should_stop(LoopState(1, 0.01, 0))
    assert stop and reason == "no_improvement"


def test_continue_when_nothing_triggers() -> None:
    stop, reason = StopCriterion().should_stop(LoopState(1, 1.0, 0))
    assert not stop and reason == ""


def test_hard_cap_priority() -> None:
    # both max_iterations and budget hold -> max_iterations reported first
    stop, reason = _crit(max_iterations=2, token_budget=10).should_stop(LoopState(2, 1.0, 50))
    assert reason == "max_iterations"


def test_from_dict_defaults_and_overrides() -> None:
    assert StopConfig.from_dict({}).max_iterations == 3
    cfg = StopConfig.from_dict(
        {"max_iterations": 5, "min_metric_improvement": 0.2, "token_budget": 10}
    )
    assert (cfg.max_iterations, cfg.min_metric_improvement, cfg.token_budget) == (5, 0.2, 10)


def test_run_loop_terminates_on_max_iterations() -> None:
    step, calls = _recording_step(1.0)
    reason = _crit(max_iterations=3).run_loop(step, tokens=lambda: 0)
    assert reason == "max_iterations"
    assert calls == [0, 1, 2]  # ran exactly max_iterations times


def test_run_loop_terminates_on_no_improvement() -> None:
    step, calls = _recording_step(0.01)
    reason = _crit(min_metric_improvement=0.05).run_loop(step, tokens=lambda: 0)
    assert reason == "no_improvement"
    assert calls == [0]  # one step, then the small improvement stops it


def test_run_loop_terminates_on_budget() -> None:
    step, calls = _recording_step(1.0)
    reason = _crit(token_budget=100).run_loop(step, tokens=lambda: 200)
    assert reason == "budget_exceeded"
    assert calls == []  # budget exceeded before any step
