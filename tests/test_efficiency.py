"""Tests for :mod:`arch_agent.services.efficiency`."""

from __future__ import annotations

from collections.abc import Callable

from arch_agent.services.efficiency import EfficiencyMeter, RunRecord


def _clock(values: list[float]) -> Callable[[], float]:
    it = iter(values)
    return lambda: next(it)


def test_accumulates_tokens_files_units_and_iterations() -> None:
    meter = EfficiencyMeter(clock=_clock([0.0]))
    meter.record_call(100, 20, files=2, units=10)
    meter.record_call(50, 5, files=1, units=4)
    meter.record_iteration()
    meter.record_iteration()
    record = meter.finish(root_cause_found=True, tests_green=True)
    assert (record.in_tokens, record.out_tokens) == (150, 25)
    assert (record.files_read, record.units_read) == (3, 14)
    assert record.iterations == 2


def test_usd_from_pricing() -> None:
    meter = EfficiencyMeter(price_in_per_mtok=3.0, price_out_per_mtok=15.0, clock=_clock([0.0]))
    meter.record_call(1_000_000, 100_000)
    assert meter.usd() == 3.0 + 0.1 * 15.0  # 4.5


def test_time_to_root_cause_with_injected_clock() -> None:
    meter = EfficiencyMeter(clock=_clock([0.0, 5.0]))  # start, then mark
    meter.mark_root_cause()
    record = meter.finish(root_cause_found=True, tests_green=True)
    assert record.time_to_root_cause_s == 5.0


def test_time_to_root_cause_none_when_not_marked() -> None:
    record = EfficiencyMeter(clock=_clock([0.0])).finish(root_cause_found=False, tests_green=False)
    assert record.time_to_root_cause_s is None
    assert record.root_cause_found is False


def test_mark_root_cause_is_idempotent() -> None:
    meter = EfficiencyMeter(clock=_clock([0.0, 5.0, 99.0]))
    meter.mark_root_cause()  # stamps 5.0
    meter.mark_root_cause()  # must NOT advance to 99.0
    assert meter.finish(root_cause_found=True, tests_green=True).time_to_root_cause_s == 5.0


def test_to_dict_is_json_shaped() -> None:
    record = EfficiencyMeter(clock=_clock([0.0])).finish(root_cause_found=True, tests_green=True)
    data = record.to_dict()
    assert set(data) == {
        "in_tokens",
        "out_tokens",
        "usd",
        "files_read",
        "units_read",
        "iterations",
        "time_to_root_cause_s",
        "root_cause_found",
        "tests_green",
    }
    assert isinstance(record, RunRecord)
