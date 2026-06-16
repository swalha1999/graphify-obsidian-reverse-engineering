"""Version constant and helpers for ArchAgent.

The package and config versions start at ``1.00`` and are validated at startup
(PRD NFR-9). These helpers parse and compare ``major.minor`` strings.
"""

from __future__ import annotations

__version__ = "1.00"


def parse_version(raw: str) -> tuple[int, int]:
    """Parse a ``major.minor`` version string into an integer tuple.

    Args:
        raw: A version string such as ``"1.00"``.

    Returns:
        A ``(major, minor)`` integer tuple.

    Raises:
        ValueError: If ``raw`` is not in ``major.minor`` form.
    """
    parts = raw.split(".")
    if len(parts) != 2:
        msg = f"expected 'major.minor', got {raw!r}"
        raise ValueError(msg)
    major, minor = parts
    return int(major), int(minor)


def is_compatible(raw: str) -> bool:
    """Return ``True`` if ``raw`` shares the package's major version."""
    return parse_version(raw)[0] == parse_version(__version__)[0]
