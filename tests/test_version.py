"""Tests for :mod:`arch_agent.version`."""

from __future__ import annotations

import pytest

from arch_agent import __version__, is_compatible, parse_version


def test_version_is_one() -> None:
    assert __version__ == "1.00"


def test_parse_version_ok() -> None:
    assert parse_version("1.00") == (1, 0)


def test_parse_version_rejects_non_pair() -> None:
    with pytest.raises(ValueError, match="major.minor"):
        parse_version("1")


def test_is_compatible_same_major() -> None:
    assert is_compatible("1.5") is True


def test_is_compatible_different_major() -> None:
    assert is_compatible("2.0") is False
