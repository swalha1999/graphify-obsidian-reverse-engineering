"""ArchAgent — token-efficient architectural analysis & refactoring agent.

Public package surface. The full service/agent layers (see ``docs/PLAN.md``)
land in later phases; this module seeds the package and exposes its version.
"""

from arch_agent.version import __version__, is_compatible, parse_version

__all__ = ["__version__", "is_compatible", "parse_version"]
