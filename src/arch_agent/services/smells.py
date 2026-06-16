"""Detect architectural smells with evidence (PRD_graph_analysis.md §4-§5).

Combines metrics + cycles + config thresholds into ranked, evidence-backed
:class:`Finding` objects: God Node, SPOF, oversized module, cyclic dependency.
"""

from __future__ import annotations

from arch_agent.services.cycles import find_cycles, find_self_loops
from arch_agent.services.findings import Finding, SmellConfig
from arch_agent.services.metrics import MetricsCalculator
from arch_agent.services.models import GraphModel

_RANK = {"high": 3, "medium": 2, "low": 1}


class SmellDetector:
    """Detect ranked architectural smells for a :class:`GraphModel`."""

    def __init__(self, config: SmellConfig | None = None) -> None:
        self._cfg = config or SmellConfig()

    def detect(self, graph: GraphModel) -> list[Finding]:
        """Return findings sorted by severity, then centrality, then node id."""
        metrics = MetricsCalculator(graph)
        centrality, fan_in, fan_out = metrics.centrality(), metrics.fan_in(), metrics.fan_out()
        findings = [
            *self._god_nodes(graph, centrality, fan_in, fan_out),
            *self._spof(graph, metrics, fan_in),
            *self._oversized(graph),
            *self._cyclic(graph),
        ]
        return sorted(
            findings,
            key=lambda f: (-_RANK[f.severity], -centrality.get(f.node, 0.0), f.node, f.smell),
        )

    def _severity(self, ratio: float) -> str:
        if ratio >= self._cfg.severity_high:
            return "high"
        if ratio >= self._cfg.severity_medium:
            return "medium"
        return "low"

    def _god_nodes(
        self,
        graph: GraphModel,
        centrality: dict[str, float],
        fan_in: dict[str, int],
        fan_out: dict[str, int],
    ) -> list[Finding]:
        cfg = self._cfg
        out: list[Finding] = []
        for nid in graph.node_ids():
            if centrality[nid] >= cfg.god_node_centrality or fan_in[nid] >= cfg.god_node_fan_in:
                ratio = max(
                    centrality[nid] / cfg.god_node_centrality if cfg.god_node_centrality else 0.0,
                    fan_in[nid] / cfg.god_node_fan_in if cfg.god_node_fan_in else 0.0,
                )
                out.append(
                    Finding(
                        "god_node",
                        nid,
                        {
                            "centrality": round(centrality[nid], 4),
                            "fan_in": fan_in[nid],
                            "fan_out": fan_out[nid],
                        },
                        self._severity(ratio),
                        f"Split {nid} into cohesive sub-modules; invert high-traffic dependencies.",
                        "High centrality / fan-in: a structural single point of failure.",
                    )
                )
        return out

    def _spof(
        self, graph: GraphModel, metrics: MetricsCalculator, fan_in: dict[str, int]
    ) -> list[Finding]:
        cfg = self._cfg
        out: list[Finding] = []
        arts = metrics.articulation_points()
        for nid in graph.node_ids():
            if nid in arts and fan_in[nid] >= cfg.spof_fan_in:
                ratio = fan_in[nid] / cfg.spof_fan_in if cfg.spof_fan_in else 0.0
                out.append(
                    Finding(
                        "spof",
                        nid,
                        {"fan_in": fan_in[nid], "is_articulation": True},
                        self._severity(ratio),
                        f"Introduce a seam so dependents don't all route through {nid}.",
                        "Articulation point with high fan-in: its removal disconnects the graph.",
                    )
                )
        return out

    def _oversized(self, graph: GraphModel) -> list[Finding]:
        cfg = self._cfg
        out: list[Finding] = []
        for node in graph.nodes:
            if node.loc is not None and node.loc > cfg.oversized_loc:
                ratio = node.loc / cfg.oversized_loc if cfg.oversized_loc else 0.0
                out.append(
                    Finding(
                        "oversized_module",
                        node.id,
                        {"loc": node.loc},
                        self._severity(ratio),
                        f"Decompose {node.id} by responsibility.",
                        f"Module exceeds the size threshold ({cfg.oversized_loc} LOC).",
                    )
                )
        return out

    def _cyclic(self, graph: GraphModel) -> list[Finding]:
        out: list[Finding] = []
        for cycle in find_cycles(graph):
            for nid in cycle:
                out.append(
                    Finding(
                        "cyclic_dependency",
                        nid,
                        {"cycle": cycle},
                        "medium",
                        "Break the cycle (dependency inversion / extract a shared interface).",
                        f"Participates in a dependency cycle: {' -> '.join(cycle)}.",
                    )
                )
        for nid in find_self_loops(graph):
            out.append(
                Finding(
                    "cyclic_dependency",
                    nid,
                    {"cycle": [nid]},
                    "low",
                    "Remove the self-dependency.",
                    "Node depends on itself.",
                )
            )
        return out
