"""Tests for :mod:`arch_agent.shared.gatekeeper`."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable

import pytest

from arch_agent.shared.gatekeeper import (
    ApiGatekeeper,
    QueueOverflowError,
    QueueStatus,
    RateLimitConfig,
)


def _no_sleep(_: float) -> None:
    return None


def _wait_for(predicate: Callable[[], bool], timeout: float = 2.0) -> None:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if predicate():
            return
        time.sleep(0.005)
    raise AssertionError("condition not met in time")


def test_executes_and_returns_result() -> None:
    assert ApiGatekeeper(sleep=_no_sleep).execute(lambda x: x + 1, 41) == 42


def test_passes_args_and_kwargs() -> None:
    assert ApiGatekeeper(sleep=_no_sleep).execute(lambda a, b: a + b, 1, b=2) == 3


def test_retries_then_succeeds() -> None:
    calls = {"n": 0}
    sleeps: list[float] = []

    def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise ValueError("boom")
        return "ok"

    gk = ApiGatekeeper(RateLimitConfig(max_attempts=5, backoff_seconds=1.0), sleep=sleeps.append)
    assert gk.execute(flaky) == "ok"
    assert calls["n"] == 3
    assert sleeps == [1.0, 2.0]  # exponential backoff between the two failures


def test_retry_exhausted_raises_last() -> None:
    sleeps: list[float] = []

    def always_fail() -> None:
        raise RuntimeError("nope")

    gk = ApiGatekeeper(RateLimitConfig(max_attempts=3, backoff_seconds=1.0), sleep=sleeps.append)
    with pytest.raises(RuntimeError, match="nope"):
        gk.execute(always_fail)
    assert len(sleeps) == 2  # between attempts 1-2 and 2-3, not after the last


def test_rate_limit_sleeps_between_calls() -> None:
    sleeps: list[float] = []
    gk = ApiGatekeeper(
        RateLimitConfig(requests_per_minute=60), sleep=sleeps.append, clock=lambda: 0.0
    )
    gk.execute(lambda: None)
    gk.execute(lambda: None)
    assert sleeps == [pytest.approx(1.0)]  # 60/min -> 1s; first call no wait


def test_rate_limit_disabled_when_rpm_zero() -> None:
    sleeps: list[float] = []
    gk = ApiGatekeeper(
        RateLimitConfig(requests_per_minute=0), sleep=sleeps.append, clock=lambda: 0.0
    )
    gk.execute(lambda: None)
    gk.execute(lambda: None)
    assert sleeps == []


def test_from_dict_reads_nested_config_and_defaults() -> None:
    cfg = RateLimitConfig.from_dict(
        {
            "requests_per_minute": 10,
            "retry": {"max_attempts": 7, "backoff_seconds": 3, "backoff_factor": 1.5},
            "queue": {"max_size": 5, "overflow": "reject"},
        }
    )
    assert cfg.requests_per_minute == 10
    assert cfg.max_attempts == 7
    assert cfg.overflow == "reject"
    assert RateLimitConfig.from_dict({}).max_attempts == 5


def test_overflow_blocks_and_status_reports_waiting() -> None:
    release = threading.Event()
    gk = ApiGatekeeper(RateLimitConfig(max_concurrent=1, requests_per_minute=0), sleep=_no_sleep)

    def blocking() -> str:
        release.wait(2.0)
        return "done"

    t1 = threading.Thread(target=lambda: gk.execute(blocking))
    t1.start()
    _wait_for(lambda: gk.get_queue_status().active == 1)

    t2 = threading.Thread(target=lambda: gk.execute(lambda: "second"))
    t2.start()
    _wait_for(lambda: gk.get_queue_status().waiting == 1)  # 2nd caller queued, no crash
    assert gk.get_queue_status() == QueueStatus(active=1, waiting=1, max_concurrent=1)

    release.set()
    t1.join(2.0)
    t2.join(2.0)
    assert not t1.is_alive() and not t2.is_alive()
    assert gk.get_queue_status() == QueueStatus(active=0, waiting=0, max_concurrent=1)


def test_overflow_reject_raises_when_full() -> None:
    release = threading.Event()
    gk = ApiGatekeeper(
        RateLimitConfig(
            max_concurrent=1, queue_max_size=0, overflow="reject", requests_per_minute=0
        ),
        sleep=_no_sleep,
    )

    def blocking() -> None:
        release.wait(2.0)

    t1 = threading.Thread(target=lambda: gk.execute(blocking))
    t1.start()
    _wait_for(lambda: gk.get_queue_status().active == 1)
    with pytest.raises(QueueOverflowError, match="queue full"):
        gk.execute(lambda: "x")  # no slot, waiting 0 >= max_size 0 -> reject
    release.set()
    t1.join(2.0)
    assert not t1.is_alive()
