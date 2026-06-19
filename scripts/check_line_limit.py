"""Fail the build if any Python file exceeds the line limit (TODO.md T7.1).

The PLAN mandates "split by responsibility; each file ≤ 150 LOC" — a guard
against modules that quietly accrete several jobs. This script enforces that
rule in CI: it counts *physical* lines (the honest, reviewer-visible size of a
file) and exits non-zero the moment one is over budget, printing every
offender so the whole backlog is visible in a single run.

Usage::

    python scripts/check_line_limit.py [PATH ...]

With no arguments it scans the tracked Python files under ``src``, ``tests``
and ``scripts``. The limit lives in one place (:data:`LIMIT`).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

LIMIT = 150
DEFAULT_ROOTS = ("src", "tests", "scripts")


def count_lines(path: Path) -> int:
    """Physical line count, robust to a missing trailing newline."""
    text = path.read_text(encoding="utf-8")
    if not text:
        return 0
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def _tracked_python_files(roots: tuple[str, ...]) -> list[Path]:
    """Tracked ``*.py`` files under ``roots`` (falls back to a filesystem walk)."""
    existing = [r for r in roots if Path(r).exists()]
    if not existing:
        return []
    try:
        # --cached + --others --exclude-standard: everything that is (or would be)
        # committed, so a brand-new file is caught before it ever lands.
        out = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "--", *existing],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        out = "\n".join(line for line in out.splitlines() if line.endswith(".py"))
        files = [Path(line) for line in out.splitlines() if line]
        if files:
            return files
    except (OSError, subprocess.CalledProcessError):
        pass
    return [p for r in existing for p in Path(r).rglob("*.py")]


def find_violations(paths: list[Path], limit: int = LIMIT) -> list[tuple[Path, int]]:
    """Return ``(path, line_count)`` for every file over ``limit``, sorted worst-first."""
    over = [(p, count_lines(p)) for p in paths if count_lines(p) > limit]
    return sorted(over, key=lambda pc: -pc[1])


def main(argv: list[str]) -> int:
    args = argv[1:]
    paths = [Path(a) for a in args] if args else _tracked_python_files(DEFAULT_ROOTS)
    violations = find_violations(paths)
    if violations:
        print(f"Files exceeding {LIMIT} LOC:")
        for path, count in violations:
            print(f"  {count:>4} {path}  (+{count - LIMIT})")
        return 1
    print(f"OK — all {len(paths)} files ≤ {LIMIT} LOC.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
