"""Load a target repository from a GitHub URL or a local path.

`RepoLoader` is the first step of the pipeline (PRD FR-1, TODO 1.1). It clones a
remote URL (shallow) or resolves an existing local directory. The git command is
injected (`CommandRunner`) so the loader is unit-testable without network access.
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Protocol

_URL_PREFIXES = ("http://", "https://", "git@", "ssh://")


def _force_remove_readonly(func: Callable[..., object], path: str, _exc: BaseException) -> None:
    """``rmtree`` handler: clear the read-only bit (Windows git packs) and retry."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


class CommandRunner(Protocol):
    """Runs a git subcommand (the args after ``git``)."""

    def __call__(self, args: Sequence[str]) -> None: ...


def _run_git(args: Sequence[str]) -> None:
    """Run ``git <args>``, raising on a non-zero exit."""
    subprocess.run(["git", *args], check=True, capture_output=True, text=True)


def is_url(source: str) -> bool:
    """Return ``True`` if ``source`` looks like a remote git URL."""
    return source.startswith(_URL_PREFIXES)


class RepoLoader:
    """Load a target repo: clone a URL into ``dest`` or resolve a local path."""

    def __init__(self, runner: CommandRunner | None = None) -> None:
        """Use ``runner`` for git calls, or a real ``git`` subprocess by default."""
        self._run = runner or _run_git

    def load(self, source: str, dest: Path, ref: str | None = None) -> Path:
        """Return a local path to the repo at ``source``.

        A URL is cloned into ``dest`` (optionally checking out ``ref``); a local
        path is resolved and returned in place.

        Raises:
            FileNotFoundError: if ``source`` is a local path that does not exist.
        """
        if is_url(source):
            return self._clone(source, dest, ref)
        return self._resolve_local(source)

    def _clone(self, url: str, dest: Path, ref: str | None) -> Path:
        """Shallow-clone ``url`` into a fresh ``dest`` directory."""
        if dest.exists():
            shutil.rmtree(dest, onexc=_force_remove_readonly)
        dest.parent.mkdir(parents=True, exist_ok=True)
        self._run(["clone", "--depth", "1", url, str(dest)])
        if ref:
            self._run(["-C", str(dest), "checkout", ref])
        return dest

    @staticmethod
    def _resolve_local(source: str) -> Path:
        """Resolve an existing local repo directory."""
        path = Path(source).expanduser().resolve()
        if not path.is_dir():
            msg = f"local repo path not found: {source}"
            raise FileNotFoundError(msg)
        return path
