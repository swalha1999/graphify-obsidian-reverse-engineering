"""Green-test + improvement gate with auto-revert (ADR-004, TODO 4.3).

A refactor is **kept only if** the target's unit tests stay green *and* the target
node's centrality improves (drops) by at least ``min_improvement``; otherwise the
change is **reverted** so behaviour is never silently broken.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from arch_agent.services.metrics import MetricsCalculator
from arch_agent.services.refactor import FileEdit, RefactorEngine
from arch_agent.services.verification import VerifyResult


class SupportsReverify(Protocol):
    """Anything that can re-graph + re-test (e.g. :class:`Reverifier`)."""

    def reverify(self, repo_path: Path, artifacts_dir: Path) -> VerifyResult: ...


@dataclass(frozen=True)
class GateResult:
    """Outcome of a gated refactor attempt."""

    kept: bool
    reason: str  # improved | tests_failed | no_improvement
    tests_passed: bool
    metric_before: float
    metric_after: float


class RefactorGate:
    """Apply a refactor and keep it only behind a green-test + improvement gate."""

    def __init__(
        self,
        engine: RefactorEngine,
        reverifier: SupportsReverify,
        repo_path: Path,
        artifacts_dir: Path,
        min_improvement: float = 0.0,
    ) -> None:
        self._engine = engine
        self._reverifier = reverifier
        self._repo = repo_path
        self._artifacts = artifacts_dir
        self._min_improvement = min_improvement

    def attempt(self, edits: list[FileEdit], target_node: str, metric_before: float) -> GateResult:
        """Apply ``edits``; keep them only if tests pass and the metric improves."""
        self._engine.apply(edits)
        result = self._reverifier.reverify(self._repo, self._artifacts)
        metric_after = MetricsCalculator(result.graph).centrality().get(target_node, 0.0)
        delta = metric_before - metric_after
        improved = metric_after < metric_before and delta >= self._min_improvement
        if not result.tests_passed:
            return self._revert("tests_failed", False, metric_before, metric_after)
        if not improved:
            return self._revert("no_improvement", True, metric_before, metric_after)
        return GateResult(True, "improved", True, metric_before, metric_after)

    def _revert(self, reason: str, tests_passed: bool, before: float, after: float) -> GateResult:
        self._engine.revert()
        return GateResult(False, reason, tests_passed, before, after)
