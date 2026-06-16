"""Apply (and revert) source edits for a refactor (PRD FR-10, TODO 4.1).

``RefactorEngine`` writes a set of :class:`FileEdit`s into the target workspace
and can revert them: it snapshots each touched file's prior content (or records
that it did not exist) before the first write, so an unwanted refactor — e.g. one
that fails the green-test gate (TODO 4.3) — leaves no trace. A "split module"
refactor is just two edits: rewrite the original file and create the new one.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FileEdit:
    """A full-content write to ``path`` (relative to the workspace)."""

    path: str
    content: str


class RefactorEngine:
    """Apply file edits to a workspace with a one-shot revert."""

    def __init__(self, workspace: Path) -> None:
        self._workspace = workspace
        # path -> prior content, or None if the file did not exist before
        self._snapshot: dict[Path, str | None] = {}

    @property
    def applied(self) -> bool:
        """True once at least one edit has been applied (and not yet reverted)."""
        return bool(self._snapshot)

    def apply(self, edits: list[FileEdit]) -> None:
        """Write each edit, snapshotting prior content on first touch."""
        for edit in edits:
            target = self._workspace / edit.path
            if target not in self._snapshot:
                self._snapshot[target] = (
                    target.read_text(encoding="utf-8") if target.is_file() else None
                )
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(edit.content, encoding="utf-8")

    def revert(self) -> None:
        """Restore every touched file to its pre-apply state."""
        for target, prior in self._snapshot.items():
            if prior is None:
                target.unlink(missing_ok=True)
            else:
                target.write_text(prior, encoding="utf-8")
        self._snapshot.clear()
