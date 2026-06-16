# Dedicated PRD — Graph Analysis (Metrics & Smell Detection)

| | |
|---|---|
| **Document** | Dedicated PRD — Graph Analysis |
| **Project** | ArchAgent |
| **Version** | 1.00 |
| **Date** | 2026-06-16 |
| **Status** | Draft — pending approval |

Companion to [`PRD.md`](PRD.md) (FR-6, FR-7) and [`PLAN.md`](PLAN.md) (§1.3 services,
§3 data contracts). Specifies the **structural metrics** and **architectural-smell rules**
with their exact inputs and outputs, so `services/metrics.py` and `services/smells.py`
(TODO 2.1–2.4, issues for 2.1/2.2/2.3/2.4) can be built test-first.

---

## 1. Purpose & Scope

Given a parsed knowledge graph, compute structural metrics and flag architectural smells
with **evidence**, deterministically and offline. This PRD covers:

- **In scope:** fan-in/out, centrality, proximity, cycle detection; the God Node / SPOF /
  oversized-module / cyclic-dependency rules; their config thresholds and output contract.
- **Out of scope:** graph *generation* (Grphify, ADR-003), the agent crew (`PRD_agent_workflow.md`),
  refactor application, and token measurement (`PRD_token_efficiency.md`).

This is **architectural** analysis over structure, not line-level logic-bug detection (ADR-001).

---

## 2. Inputs

### 2.1 Graph model (from `GraphLoader`, TODO 1.4)

Parsed from `graph.json` into typed models (`models.py`, TODO 1.3). Illustrative schema:

```jsonc
{
  "version": "1.00",
  "nodes": [ { "id": "mod.payments", "type": "module", "loc": 412, "centrality": 0.91 } ],
  "edges": [ { "src": "mod.api", "dst": "mod.payments", "kind": "import" } ]
}
```

- `type ∈ {module, class, function}`; `kind ∈ {import, call, inherit}`.
- `loc` and `centrality` are **optional** in the source file. The loader is defensive
  (missing optional fields default; unknown fields ignored). When `centrality` is absent we
  **compute** it (§3.2); when present it is treated as advisory and our computed value is canonical.
- Directionality: an edge `src → dst` means *src depends on dst*.

### 2.2 Configuration (from `config/setup.json`, ADR-005, versioned 1.00)

All thresholds are config-driven — **no hard-coded values** (NFR-2). Illustrative defaults:

```jsonc
{
  "version": "1.00",
  "graph_analysis": {
    "god_node_centrality": 0.50,   // normalised degree centrality
    "god_node_fan_in": 20,         // incoming dependencies
    "spof_fan_in": 15,
    "oversized_loc": 300,          // LOC for a target-repo module
    "proximity_max_hops": 4,       // suspects within N hops of the seed set
    "severity_bands": { "medium": 1.5, "high": 2.0 }  // value / threshold ratio
  }
}
```

---

## 3. Metrics Specification

All metrics are pure functions of the graph (deterministic; stable ordering by node id).
`N` = node count, `E` = edge count.

### 3.1 Fan-in / Fan-out
- **Definition:** `fan_in(n)` = count of edges with `dst == n`; `fan_out(n)` = count with `src == n`.
- **Input:** `GraphModel`. **Output:** `dict[node_id, int]` for each.
- **Algorithm:** single pass over edges, O(E). Self-loops counted once on each side.

### 3.2 Degree centrality (primary)
- **Definition:** `centrality(n) = (fan_in(n) + fan_out(n)) / (N - 1)`, normalised to `[0, 1]`
  (`0.0` when `N <= 1`).
- **Input:** `GraphModel`. **Output:** `dict[node_id, float]`.
- **Algorithm:** derive from fan-in/out, O(N + E). This is the canonical centrality used by the
  smell rules. *(Optional stretch: Brandes betweenness for cross-checking God Nodes — see §6.)*

### 3.3 Proximity
- **Definition:** `proximity(n, seed)` = shortest **undirected** hop distance from `n` to the
  nearest node in a `seed` set (e.g. nodes touching failing tests, or a chosen suspect).
  Normalised form: `1 / (1 + dist)`; unreachable ⇒ `dist = ∞`, proximity `0.0`.
- **Input:** `GraphModel`, `seed: set[node_id]`. **Output:** `dict[node_id, int]` (hops) and the
  normalised float.
- **Algorithm:** multi-source BFS from `seed`, O(N + E).

### 3.4 Cycle detection
- **Definition:** maximal groups of mutually reachable nodes — strongly connected components
  (SCCs) of size `> 1`; each is a dependency cycle. Self-loops (`src == dst`) are reported separately.
- **Input:** `GraphModel`. **Output:** `list[list[node_id]]` (each inner list is one cycle, node
  ids sorted for determinism).
- **Algorithm:** Tarjan's SCC, O(N + E).

---

## 4. Smell-Detection Rules

Each rule consumes the metrics above + config thresholds and emits zero or more `Finding`
objects (§5). Severity is `value / threshold` mapped through `severity_bands`
(`< medium` ⇒ `low`, `>= medium` ⇒ `medium`, `>= high` ⇒ `high`).

| Smell | Trigger (config-driven) | Evidence | Default recommendation |
|---|---|---|---|
| **God Node** | `centrality(n) >= god_node_centrality` **or** `fan_in(n) >= god_node_fan_in` | `centrality`, `fan_in`, `fan_out` | Split `n` into cohesive sub-modules; invert high-traffic dependencies. |
| **SPOF** | `n` is an articulation point (its removal disconnects the undirected graph) **and** `fan_in(n) >= spof_fan_in` | `fan_in`, `is_articulation` | Introduce an abstraction/seam so dependents don't all route through `n`. |
| **Oversized module** | `loc(n) > oversized_loc` (skipped if `loc` absent) | `loc` | Decompose by responsibility until each unit is cohesive. |
| **Cyclic dependency** | `n` participates in an SCC of size `> 1` (or a self-loop) | `cycle` (the node list) | Break the cycle (dependency inversion / extract shared interface). |

- **Articulation points** (for SPOF) are found with a single DFS, O(N + E).
- A node may match multiple smells ⇒ multiple findings (one per smell).
- Thresholds, not magic numbers: every comparison reads from §2.2.

---

## 5. Output Contract

A `Finding` (aligns with `PLAN.md` §3.2 `RecommendationReport.findings[]`):

```jsonc
{
  "smell": "god_node",                       // god_node | spof | oversized_module | cyclic_dependency
  "node": "mod.payments",
  "evidence": { "centrality": 0.91, "fan_in": 37, "fan_out": 4 },
  "severity": "high",                        // low | medium | high
  "recommendation": "Split mod.payments into payments.core + payments.io",
  "rationale": "Single point of failure; high coupling."
}
```

- **`detect_smells(graph, config) -> list[Finding]`** is the public surface (exposed via the SDK,
  PRD FR-15).
- **Ordering:** sorted by severity (`high > medium > low`), then descending `centrality`, then
  `node` id — fully deterministic.
- Empty graph ⇒ `[]` (never raises).

---

## 6. Determinism, Edge Cases & Extensions

- **Determinism:** stable sort everywhere; node iteration ordered by id. Same graph ⇒ same findings.
- **Edge cases:** empty/one-node graph (centrality `0.0`, no findings); missing `loc`
  (oversized rule skipped for that node); disconnected components (BFS/DFS handle per component);
  unknown node `type` or edge `kind` ignored by the loader before analysis.
- **Extensions (FR-17 candidates, optional):** Brandes betweenness as a second God-Node signal;
  rank suspects by `proximity` to failing tests; orphan-component detection (in-degree `0` and
  out-degree `0`); a blast-radius/impact count (reachable dependents of `n`).

---

## 7. Testing (TDD, PRD §7 / NFR-4)

A fixture `graph.json` with **known** structure drives unit tests with **hand-computed** expectations:

- a God Node (high fan-in hub), an oversized module (`loc` over threshold),
- an explicit cycle `A → B → C → A`, and an articulation point for SPOF.

Assertions: fan-in/out counts, centrality values, the detected cycle, articulation set, and the
exact ordered `list[Finding]` (smell, node, severity, evidence). Coverage ≥ 85 % (the global gate).

---

## 8. Traceability

| This PRD | Satisfies |
|---|---|
| §3 metrics | PRD **FR-6**; TODO **2.1**, **2.2** |
| §4 smell rules | PRD **FR-7**; TODO **2.3** |
| §5 output contract | `PLAN.md` §3.2; feeds the crew (`PRD_agent_workflow.md`) and `ReverseEngineer` (TODO 2.4) |
| §2.2 config thresholds | ADR-005 (config-driven, versioned) |
