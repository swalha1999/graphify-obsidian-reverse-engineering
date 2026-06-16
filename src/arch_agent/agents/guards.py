"""Guard that agents reason over graph artifacts, never raw source (FR 3.5, ADR-001).

A whole-file code dump is detected heuristically by counting strong Python-source
signals (``import``/``from`` statements, ``def`` with a call signature, ``class``
with ``(``/``:``). Markdown graph artifacts (``index.md``, ``hot.md``), finding
summaries, and Mermaid diagrams (e.g. ``class Foo`` without ``:``) do not trip it.
"""

from __future__ import annotations

import re

_SIGNALS = (
    re.compile(r"^\s*def\s+\w+\s*\("),
    re.compile(r"^\s*class\s+\w+\s*[(:]"),
    re.compile(r"^\s*(?:import|from)\s+\w"),
)
_DEFAULT_MIN_SIGNALS = 3


class RawSourceError(ValueError):
    """Raised when a prompt/context looks like a raw-source dump."""


def count_source_signals(text: str) -> int:
    """Count lines that look like Python source declarations."""
    return sum(1 for line in text.splitlines() if any(p.match(line) for p in _SIGNALS))


def looks_like_raw_source(text: str, *, min_signals: int = _DEFAULT_MIN_SIGNALS) -> bool:
    """True if ``text`` carries at least ``min_signals`` raw-source signals."""
    return count_source_signals(text) >= min_signals


def assert_graph_only(text: str, *, min_signals: int = _DEFAULT_MIN_SIGNALS) -> None:
    """Raise :class:`RawSourceError` if ``text`` looks like a raw-source dump."""
    signals = count_source_signals(text)
    if signals >= min_signals:
        raise RawSourceError(
            f"prompt contains {signals} raw-source signals; agents must reason over "
            "graph artifacts (index.md / hot.md / findings), not whole files"
        )
