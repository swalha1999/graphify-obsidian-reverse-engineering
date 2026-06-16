"""Refactor-loop stop criterion (PRD FR-12, PRD_agent_workflow.md §6, TODO 4.4).

The loop ends when **any** condition holds — max iterations reached, the last
iteration's metric improvement fell below the threshold, or the token budget was
exceeded. All thresholds are config-driven (``config/setup.json`` →
``agent_workflow``), and :meth:`StopCriterion.run_loop` is guaranteed to
terminate because the iteration count strictly increases toward a hard cap.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class StopConfig:
    """Config-driven loop limits (PRD_agent_workflow §6)."""

    max_iterations: int = 3
    min_metric_improvement: float = 0.05
    token_budget: int = 200_000

    @classmethod
    def from_dict(cls, cfg: dict[str, Any]) -> StopConfig:
        """Build from an ``agent_workflow`` config dict, falling back to defaults."""
        return cls(
            max_iterations=int(cfg.get("max_iterations", cls.max_iterations)),
            min_metric_improvement=float(
                cfg.get("min_metric_improvement", cls.min_metric_improvement)
            ),
            token_budget=int(cfg.get("token_budget", cls.token_budget)),
        )


@dataclass(frozen=True)
class LoopState:
    """A snapshot of loop progress used to decide whether to stop."""

    iteration: int  # completed iterations
    last_improvement: float  # metric improvement from the most recent iteration
    tokens_used: int


class StopCriterion:
    """Decide when the refactor loop should stop (deterministic, config-driven)."""

    def __init__(self, config: StopConfig | None = None) -> None:
        self._cfg = config or StopConfig()

    def should_stop(self, state: LoopState) -> tuple[bool, str]:
        """Return ``(stop, reason)``; hard caps take priority over diminishing returns."""
        if state.iteration >= self._cfg.max_iterations:
            return True, "max_iterations"
        if state.tokens_used >= self._cfg.token_budget:
            return True, "budget_exceeded"
        if state.last_improvement < self._cfg.min_metric_improvement:
            return True, "no_improvement"
        return False, ""

    def run_loop(self, step: Callable[[int], float], tokens: Callable[[], int]) -> str:
        """Run ``step(iteration)`` until a stop condition; return the stop reason.

        ``step`` performs one refactor iteration and returns its metric improvement;
        ``tokens`` reports cumulative token usage. Always terminates.
        """
        iteration = 0
        last_improvement = float("inf")  # never "no improvement" before the first step
        while True:
            stop, reason = self.should_stop(LoopState(iteration, last_improvement, tokens()))
            if stop:
                return reason
            last_improvement = step(iteration)
            iteration += 1
