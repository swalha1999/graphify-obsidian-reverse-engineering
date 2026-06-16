"""Centralised gateway for all external (LLM) calls (PRD FR-16, PRD_agent_workflow §8).

Every call is routed through :meth:`ApiGatekeeper.execute`, which **rate-limits**,
bounds **concurrency** (overflow callers queue/block rather than crash — or are
rejected if so configured), **retries** with exponential backoff, and **logs**.
``sleep`` and ``clock`` are injectable so tests need no real time.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

_T = TypeVar("_T")
_LOG = logging.getLogger("arch_agent.gatekeeper")


@dataclass(frozen=True)
class RateLimitConfig:
    """Gatekeeper limits (mirrors ``config/rate_limits.json``)."""

    requests_per_minute: int = 50
    max_concurrent: int = 4
    max_attempts: int = 5
    backoff_seconds: float = 2.0
    backoff_factor: float = 2.0
    queue_max_size: int = 100
    overflow: str = "block"  # block | reject

    @classmethod
    def from_dict(cls, cfg: dict[str, Any]) -> RateLimitConfig:
        """Build from a ``rate_limits.json`` dict, falling back to defaults."""
        retry = cfg.get("retry", {})
        queue = cfg.get("queue", {})
        return cls(
            requests_per_minute=int(cfg.get("requests_per_minute", cls.requests_per_minute)),
            max_concurrent=int(cfg.get("max_concurrent", cls.max_concurrent)),
            max_attempts=int(retry.get("max_attempts", cls.max_attempts)),
            backoff_seconds=float(retry.get("backoff_seconds", cls.backoff_seconds)),
            backoff_factor=float(retry.get("backoff_factor", cls.backoff_factor)),
            queue_max_size=int(queue.get("max_size", cls.queue_max_size)),
            overflow=str(queue.get("overflow", cls.overflow)),
        )


@dataclass(frozen=True)
class QueueStatus:
    """A snapshot of in-flight and waiting calls."""

    active: int
    waiting: int
    max_concurrent: int


class QueueOverflowError(RuntimeError):
    """Raised when the queue is full and the overflow policy is ``reject``."""


class ApiGatekeeper:
    """Rate-limit, queue, retry, and log every external call."""

    def __init__(
        self,
        config: RateLimitConfig | None = None,
        *,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._cfg = config or RateLimitConfig()
        self._sleep = sleep
        self._clock = clock
        self._sem = threading.BoundedSemaphore(self._cfg.max_concurrent)
        self._lock = threading.Lock()
        self._rate_lock = threading.Lock()
        rpm = self._cfg.requests_per_minute
        self._min_interval = 60.0 / rpm if rpm > 0 else 0.0
        self._next_allowed = 0.0
        self._active = 0
        self._waiting = 0

    def execute(self, func: Callable[..., _T], *args: Any, **kwargs: Any) -> _T:
        """Run ``func`` through the gatekeeper and return its result."""
        if not self._sem.acquire(blocking=False):
            self._enter_queue_or_reject()
            try:
                self._sem.acquire()
            finally:
                with self._lock:
                    self._waiting -= 1
        with self._lock:
            self._active += 1
        try:
            self._rate_limit()
            return self._run_with_retry(func, *args, **kwargs)
        finally:
            with self._lock:
                self._active -= 1
            self._sem.release()

    def get_queue_status(self) -> QueueStatus:
        """Return the current active/waiting snapshot."""
        with self._lock:
            return QueueStatus(self._active, self._waiting, self._cfg.max_concurrent)

    def _enter_queue_or_reject(self) -> None:
        with self._lock:
            if self._cfg.overflow == "reject" and self._waiting >= self._cfg.queue_max_size:
                raise QueueOverflowError(f"queue full (max_size={self._cfg.queue_max_size})")
            self._waiting += 1

    def _rate_limit(self) -> None:
        if self._min_interval <= 0:
            return
        with self._rate_lock:
            now = self._clock()
            wait = self._next_allowed - now
            if wait > 0:
                self._sleep(wait)
                now = self._clock()
            self._next_allowed = max(now, self._next_allowed) + self._min_interval

    def _run_with_retry(self, func: Callable[..., _T], *args: Any, **kwargs: Any) -> _T:
        delay = self._cfg.backoff_seconds
        last_exc: Exception | None = None
        for attempt in range(1, self._cfg.max_attempts + 1):
            try:
                result = func(*args, **kwargs)
            except Exception as exc:
                last_exc = exc
                _LOG.warning(
                    "gatekeeper call failed (attempt %d/%d): %s",
                    attempt,
                    self._cfg.max_attempts,
                    exc,
                )
                if attempt < self._cfg.max_attempts:
                    self._sleep(delay)
                    delay *= self._cfg.backoff_factor
            else:
                _LOG.debug("gatekeeper call ok on attempt %d", attempt)
                return result
        assert last_exc is not None
        raise last_exc
