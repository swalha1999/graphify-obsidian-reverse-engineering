"""Fail the build if a secret is committed (TODO.md T7.4; PRD NFR-3).

Two guards, both of which must be GREEN:

1. **Hygiene** — ``.env-example`` is committed (so contributors know which keys to
   set) and ``.env`` itself is *not* tracked (real secrets live in the environment
   only, never in git).
2. **Content scan** — no tracked text file contains a high-confidence secret:
   provider API keys, cloud credentials, or a private-key block.

The patterns are deliberately specific so false positives stay near zero —
placeholder values such as ``sk-test-not-real`` do not match. Run with no
arguments in CI; exits non-zero (and prints every hit) if anything is found.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

# (label, pattern) — each matches a real credential format, not a placeholder.
SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("Anthropic API key", re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}")),
    ("OpenAI API key", re.compile(r"sk-[A-Za-z0-9]{40,}")),
    ("AWS access key id", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("Google API key", re.compile(r"AIza[0-9A-Za-z_-]{35}")),
    ("GitHub token", re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}")),
    ("Slack token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("Private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
]

# Binary / vendored files we never scan (the lockfile holds harmless hashes).
SKIP_SUFFIXES = {".jpg", ".jpeg", ".png", ".gif", ".pdf", ".ico", ".lock"}


def _tracked_files() -> list[Path]:
    """All git-tracked paths (falls back to a filesystem walk outside git)."""
    try:
        out = subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True).stdout
        return [Path(line) for line in out.splitlines() if line]
    except (OSError, subprocess.CalledProcessError):
        return [p for p in Path().rglob("*") if p.is_file()]


def scan_file(path: Path) -> list[tuple[int, str]]:
    """Return ``(line_number, label)`` for every secret pattern hit in ``path``."""
    if path.suffix.lower() in SKIP_SUFFIXES:
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return []  # unreadable or binary -> nothing to scan
    return [
        (n, label)
        for n, line in enumerate(lines, start=1)
        for label, pattern in SECRET_PATTERNS
        if pattern.search(line)
    ]


def hygiene_errors(files: list[Path]) -> list[str]:
    """Structural checks: ``.env-example`` present and ``.env`` not tracked."""
    errors: list[str] = []
    if not Path(".env-example").is_file():
        errors.append(".env-example is missing (commit a template with empty values).")
    if Path(".env") in files:
        errors.append(".env is tracked by git — remove it; secrets belong in env only.")
    return errors


def main() -> int:
    files = _tracked_files()
    errors = hygiene_errors(files)
    findings = [(path, n, label) for path in files for n, label in scan_file(path)]
    if findings:
        errors.append(f"{len(findings)} potential secret(s) in tracked files:")
        errors.extend(f"  {path}:{n}  {label}" for path, n, label in findings)
    if errors:
        print("Secret scan FAILED:")
        for line in errors:
            print(f"  {line}" if not line.startswith("  ") else line)
        return 1
    print(f"OK — no secrets found across {len(files)} tracked files; .env-example present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
