"""Re-graph and re-test the target after a change (PRD FR-11, TODO 4.2).

After a refactor, :class:`Reverifier` re-runs Grphify (to get the updated graph)
and the target's unit tests, returning both outcomes. The test command is
injected (``TestRunner``) because targets differ — the default runs ``pytest``,
but BugsInPy projects supply their own command.
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from arch_agent.infra.grphify_runner import GrphifyRunner
from arch_agent.services.graph_loader import GraphLoader
from arch_agent.services.models import GraphModel

TestRunner = Callable[[Path], bool]


def _run_pytest(repo_path: Path) -> bool:
    """Run ``pytest`` in ``repo_path``; True if the suite passes."""
    completed = subprocess.run(
        ["pytest", "-q"], cwd=str(repo_path), capture_output=True, text=True, check=False
    )
    return completed.returncode == 0


@dataclass(frozen=True)
class VerifyResult:
    """Outcome of re-graphing and re-testing after a change."""

    tests_passed: bool
    graph: GraphModel


class Reverifier:
    """Re-run Grphify and the unit tests after a change."""

    def __init__(
        self,
        grphify: GrphifyRunner | None = None,
        loader: GraphLoader | None = None,
        test_runner: TestRunner = _run_pytest,
    ) -> None:
        self._grphify = grphify or GrphifyRunner()
        self._loader = loader or GraphLoader()
        self._test_runner = test_runner

    def reverify(self, repo_path: Path, artifacts_dir: Path) -> VerifyResult:
        """Re-graph the repo, reload the model, and run the unit tests."""
        graph_path = self._grphify.run(repo_path, artifacts_dir)
        graph = self._loader.load(graph_path)
        passed = self._test_runner(repo_path)
        return VerifyResult(tests_passed=passed, graph=graph)
