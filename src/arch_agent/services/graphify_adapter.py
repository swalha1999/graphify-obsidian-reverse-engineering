"""Normalise graphify's node-link ``graph.json`` into the PLAN schema (PLAN §3.1).

graphify emits NetworkX **node-link** JSON: edges live under ``links`` as
``source``/``target``, and nodes carry ``id``/``label``/``file_type`` but no
``type``. This maps it to ``{version, nodes:[{id,type}], edges:[{src,dst,kind}]}``
which the defensive :class:`GraphLoader` understands. Node ``type`` is inferred
from the label (``foo()`` → function, ``x.py`` → module, ``Name`` → class), and
non-code nodes (graphify "rationale"/doc extractions) are dropped.
"""

from __future__ import annotations

from typing import Any

_EDGE_KINDS = ("import", "call", "inherit")


def is_graphify(data: dict[str, Any]) -> bool:
    """True if ``data`` looks like graphify node-link output (``links``, no ``edges``)."""
    return "links" in data and "edges" not in data


def normalize(data: dict[str, Any]) -> dict[str, Any]:
    """Convert graphify node-link JSON to the PLAN ``{nodes, edges}`` schema."""
    raw_nodes = (n for n in data.get("nodes", []) if isinstance(n, dict))
    nodes = [n for n in (_node(item) for item in raw_nodes) if n is not None]
    ids = {n["id"] for n in nodes}
    raw_links = (e for e in data.get("links", []) if isinstance(e, dict))
    edges = [e for e in (_edge(item, ids) for item in raw_links) if e is not None]
    return {"version": "1.00", "nodes": nodes, "edges": edges}


def _node(item: dict[str, Any]) -> dict[str, Any] | None:
    node_id = item.get("id")
    if not isinstance(node_id, str) or not node_id:
        return None
    node_type = _infer_type(item)
    if node_type is None:
        return None
    return {"id": node_id, "type": node_type}


def _infer_type(item: dict[str, Any]) -> str | None:
    if item.get("file_type") not in (None, "code"):
        return None  # rationale / doc nodes are not architecture
    label = str(item.get("label") or item.get("id") or "")
    if label.endswith("()"):
        return "function"
    if label.endswith(".py"):
        return "module"
    if label[:1].isupper():
        return "class"
    return "module"


def _edge(item: dict[str, Any], ids: set[str]) -> dict[str, Any] | None:
    src, dst = item.get("source"), item.get("target")
    if src not in ids or dst not in ids:
        return None
    kind = item.get("kind") or item.get("relation") or "call"
    if kind not in _EDGE_KINDS:
        kind = "call"
    return {"src": src, "dst": dst, "kind": kind}
