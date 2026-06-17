"""Token + cost accounting for one run (PRD FR-13, PRD_token_efficiency.md §4-§5).

``EfficiencyMeter`` accumulates the metrics the study compares per run — tokens
(in/out + USD), files/textual units read, iterations, and time/quality to reach
the root cause — and emits a :class:`RunRecord`. USD is derived from per-model
prices (``config/setup.json`` → ``model.pricing_usd_per_mtok``); ``clock`` is
injectable so timing is deterministic in tests.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from typing import Any

_PER_MILLION = 1_000_000


@dataclass(frozen=True)
class RunRecord:
    """One run's measured efficiency metrics (PLAN.md §3.3)."""

    in_tokens: int
    out_tokens: int
    usd: float
    files_read: int
    units_read: int
    iterations: int
    time_to_root_cause_s: float | None
    root_cause_found: bool
    tests_green: bool

    def to_dict(self) -> dict[str, Any]:
        """A JSON-serialisable view of the record."""
        return asdict(self)


class EfficiencyMeter:
    """Accumulate per-run efficiency metrics, then emit a :class:`RunRecord`."""

    def __init__(
        self,
        price_in_per_mtok: float = 0.0,
        price_out_per_mtok: float = 0.0,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._price_in = price_in_per_mtok
        self._price_out = price_out_per_mtok
        self._clock = clock
        self._in = 0
        self._out = 0
        self._files = 0
        self._units = 0
        self._iterations = 0
        self._start = clock()
        self._root_cause_at: float | None = None

    def record_call(
        self, in_tokens: int, out_tokens: int, *, files: int = 0, units: int = 0
    ) -> None:
        """Record one LLM call's token usage and how much context it read."""
        self._in += in_tokens
        self._out += out_tokens
        self._files += files
        self._units += units

    def record_iteration(self) -> None:
        """Count one investigation/refactor round."""
        self._iterations += 1

    def mark_root_cause(self) -> None:
        """Stamp the moment the root cause was reached (first call wins)."""
        if self._root_cause_at is None:
            self._root_cause_at = self._clock()

    def usd(self) -> float:
        """Cost so far from accumulated tokens and per-model prices."""
        return self._in / _PER_MILLION * self._price_in + self._out / _PER_MILLION * self._price_out

    def finish(self, *, root_cause_found: bool, tests_green: bool) -> RunRecord:
        """Build the immutable record for this run."""
        ttrc = None if self._root_cause_at is None else self._root_cause_at - self._start
        return RunRecord(
            in_tokens=self._in,
            out_tokens=self._out,
            usd=self.usd(),
            files_read=self._files,
            units_read=self._units,
            iterations=self._iterations,
            time_to_root_cause_s=ttrc,
            root_cause_found=root_cause_found,
            tests_green=tests_green,
        )
