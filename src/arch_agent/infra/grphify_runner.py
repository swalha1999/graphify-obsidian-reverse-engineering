"""Run Graphify and collect its artifacts (PRD FR-2, ADR-003).

Two facts about the ``graphify`` CLI shape this wrapper:

1. ``graphify extract`` writes ``graphify-out/`` **inside the target directory**
   (not the cwd).
2. It routes any non-code file (docs/papers/images) to a **paid LLM backend**; a
   pure-code corpus extracts for free via AST with no key.

So we stage a **code-only** copy of the repo (excluding docs/images and
``.git``/``graphify-out``), run extraction over that, and lift the outputs into
``artifacts/``. The command is injected (``CommandRunner``) for tests.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

_OUTPUT_DIR = "graphify-out"
_ARTIFACTS = ("graph.json", "GRAPH_REPORT.md", "graph.html")
_NON_CODE = {".md", ".rst", ".txt", ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
_SKIP_DIRS = {_OUTPUT_DIR, ".git"}


class CommandRunner(Protocol):
    """Runs a ``graphify`` subcommand (the args after ``graphify``) in ``cwd``."""

    def __call__(self, args: Sequence[str], cwd: Path) -> None: ...


def _run_graphify(args: Sequence[str], cwd: Path) -> None:
    """Run ``graphify <args>`` in ``cwd``, raising on a non-zero exit."""
    subprocess.run(["graphify", *args], check=True, capture_output=True, text=True, cwd=str(cwd))


def _ignore(_dir: str, names: list[str]) -> set[str]:
    """``copytree`` filter: drop non-code files and ``.git``/``graphify-out``."""
    return {n for n in names if Path(n).suffix.lower() in _NON_CODE} | _SKIP_DIRS


class GrphifyRunner:
    """Stage a code-only copy, run ``graphify extract``, collect into ``artifacts/``."""

    def __init__(self, runner: CommandRunner | None = None) -> None:
        """Use ``runner`` for CLI calls, or a real ``graphify`` subprocess by default."""
        self._run = runner or _run_graphify

    def run(self, repo_path: Path, artifacts_dir: Path) -> Path:
        """Extract a knowledge graph from ``repo_path``; return the ``graph.json`` path.

        Raises:
            FileNotFoundError: if graphify did not produce a ``graph.json``.
        """
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            staged = Path(tmp) / "code"
            shutil.copytree(repo_path, staged, ignore=_ignore)
            self._run(["extract", str(staged)], cwd=staged)
            out_dir = staged / _OUTPUT_DIR
            if not (out_dir / "graph.json").is_file():
                msg = f"graphify produced no graph.json under {out_dir}"
                raise FileNotFoundError(msg)
            return self._collect(out_dir, artifacts_dir)

    @staticmethod
    def _collect(out_dir: Path, artifacts_dir: Path) -> Path:
        """Copy known artifacts into ``artifacts_dir``; return the graph.json path."""
        for name in _ARTIFACTS:
            src = out_dir / name
            if src.is_file():
                shutil.copy2(src, artifacts_dir / name)
        return artifacts_dir / "graph.json"
