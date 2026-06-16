"""Run Graphify (the ``graphify`` CLI) and collect its artifacts.

Wraps ``graphify extract`` as a subprocess (ADR-003, PRD FR-2). The rest of the
system depends only on the files it emits — ``graph.json``, ``GRAPH_REPORT.md``,
``graph.html`` — so this is the single seam to the external tool. The command is
injected (``CommandRunner``) so unit tests run without the CLI or an API key.

See ``docs/GRAPHIFY_SETUP.md``. Graphify writes into a ``graphify-out/`` directory;
we run it with ``cwd = artifacts_dir`` so that directory lands under ``artifacts/``,
then lift the key files up into ``artifacts/`` itself.
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

_OUTPUT_DIR = "graphify-out"
_ARTIFACTS = ("graph.json", "GRAPH_REPORT.md", "graph.html")


class CommandRunner(Protocol):
    """Runs a ``graphify`` subcommand (the args after ``graphify``) in ``cwd``."""

    def __call__(self, args: Sequence[str], cwd: Path) -> None: ...


def _run_graphify(args: Sequence[str], cwd: Path) -> None:
    """Run ``graphify <args>`` in ``cwd``, raising on a non-zero exit."""
    subprocess.run(["graphify", *args], check=True, capture_output=True, text=True, cwd=str(cwd))


class GrphifyRunner:
    """Invoke ``graphify extract`` and copy its outputs into ``artifacts/``."""

    def __init__(self, runner: CommandRunner | None = None) -> None:
        """Use ``runner`` for CLI calls, or a real ``graphify`` subprocess by default."""
        self._run = runner or _run_graphify

    def run(self, repo_path: Path, artifacts_dir: Path) -> Path:
        """Extract a knowledge graph from ``repo_path`` into ``artifacts_dir``.

        Returns the path to the produced ``graph.json``.

        Raises:
            FileNotFoundError: if graphify did not produce a ``graph.json``.
        """
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        self._run(["extract", str(repo_path)], cwd=artifacts_dir)
        out_dir = artifacts_dir / _OUTPUT_DIR
        if not (out_dir / "graph.json").is_file():
            msg = f"graphify produced no graph.json under {out_dir}"
            raise FileNotFoundError(msg)
        return self._collect(out_dir, artifacts_dir)

    @staticmethod
    def _collect(out_dir: Path, artifacts_dir: Path) -> Path:
        """Copy known artifacts up into ``artifacts_dir``; return the graph.json path."""
        for name in _ARTIFACTS:
            src = out_dir / name
            if src.is_file():
                shutil.copy2(src, artifacts_dir / name)
        return artifacts_dir / "graph.json"
