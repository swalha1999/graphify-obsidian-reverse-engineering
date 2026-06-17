"""Load and version-validate the JSON config (PRD NFR-2/NFR-9, ADR-005).

``config/setup.json`` and ``config/rate_limits.json`` must declare
``"version": "1.00"`` — validated at startup so a stale config fails fast rather
than silently. Typed accessors expose the values the SDK needs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

EXPECTED_VERSION = "1.00"


@dataclass(frozen=True)
class Config:
    """Parsed, version-checked configuration."""

    setup: dict[str, Any]
    rate_limits: dict[str, Any]

    @property
    def target_repo(self) -> str:
        return str(self.setup["target_repo"]["url"])

    @property
    def model(self) -> str:
        return str(self.setup["model"]["name"])

    @property
    def max_tokens(self) -> int:
        return int(self.setup["model"].get("max_tokens", 4096))

    @property
    def graph_analysis(self) -> dict[str, Any]:
        return dict(self.setup.get("graph_analysis", {}))

    @property
    def agent_workflow(self) -> dict[str, Any]:
        return dict(self.setup.get("agent_workflow", {}))

    @property
    def paths(self) -> dict[str, Any]:
        return dict(self.setup.get("paths", {}))


def load_config(config_dir: Path) -> Config:
    """Load and version-validate ``setup.json`` + ``rate_limits.json``."""
    return Config(
        setup=_load_versioned(config_dir / "setup.json"),
        rate_limits=_load_versioned(config_dir / "rate_limits.json"),
    )


def _load_versioned(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: expected a JSON object")
    version = data.get("version")
    if version != EXPECTED_VERSION:
        raise ValueError(f"{path.name}: expected version {EXPECTED_VERSION!r}, got {version!r}")
    return data
