"""Finding output + SmellConfig input for smell detection (PRD_graph_analysis §2.2/§5)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Finding:
    """One detected architectural smell, with evidence (PRD_graph_analysis §5)."""

    smell: str  # god_node | spof | oversized_module | cyclic_dependency
    node: str
    evidence: dict[str, object]
    severity: str  # low | medium | high
    recommendation: str
    rationale: str


@dataclass(frozen=True)
class SmellConfig:
    """Config-driven thresholds for the smell rules (PRD_graph_analysis §2.2)."""

    god_node_centrality: float = 0.5
    god_node_fan_in: int = 20
    spof_fan_in: int = 15
    oversized_loc: int = 300
    severity_medium: float = 1.5
    severity_high: float = 2.0

    @classmethod
    def from_dict(cls, cfg: dict[str, Any]) -> SmellConfig:
        """Build from a ``graph_analysis`` config dict, falling back to defaults."""
        bands = cfg.get("severity_bands", {})
        return cls(
            god_node_centrality=float(cfg.get("god_node_centrality", cls.god_node_centrality)),
            god_node_fan_in=int(cfg.get("god_node_fan_in", cls.god_node_fan_in)),
            spof_fan_in=int(cfg.get("spof_fan_in", cls.spof_fan_in)),
            oversized_loc=int(cfg.get("oversized_loc", cls.oversized_loc)),
            severity_medium=float(bands.get("medium", cls.severity_medium)),
            severity_high=float(bands.get("high", cls.severity_high)),
        )
