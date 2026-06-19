# Findings — `martinpeck/broken-python` (Opus 4.8)

| | |
|---|---|
| **Target** | [`martinpeck/broken-python`](https://github.com/martinpeck/broken-python) (`master`) |
| **Model** | `claude-opus-4-8` (Opus 4.8) |
| **Date** | 2026-06-19 |
| **Why this repo** | Biggest *graphable* target in the assignment §3 list — 5 modules / 446 LOC, ~4× the buggy-python default (`soarsmu/BugsInPy` is larger by description but ships only 1 raw `.py` file, so Graphify's AST extractor sees nothing). |

## How it was run

1. `graphify extract` (code-only staging) → AST knowledge graph.
2. `graphify cluster-only --backend claude --model claude-opus-4-8` → communities + report + HTML.
3. ArchAgent pipeline over the graph: smell detection → reverse-engineering → LangGraph agent crew (Opus) → baseline-vs-graph-guided token study (Opus).

> Graphify's **community-naming** step needs the `graphifyy[anthropic]` extra (absent from its isolated tool env), so cluster labels fell back to `Community N` placeholders. The graph topology and every ArchAgent (Opus) output are unaffected.

## Graph

- **Graphify:** 19 nodes · 15 edges · 6 communities (100% AST-extracted, 0 inferred).
- **ArchAgent loader (defensive parse):** 16 nodes (5 modules, 2 classes, 9 functions) · 12 call edges.

## Structural findings

- **God Node + SPOF — `Polygon` class** (`polygons_polygons_polygon`): highest degree centrality (0.27), top fan-in (2), and an **articulation point** — removing it disconnects the graph. Graphify independently flags `Polygon` as the #1 God Node and a cross-community bridge (betweenness 0.085).
- **Other articulation points (SPOFs):** `polygons_polygons`, `mathsquiz_mathsquiz_step2`, `mathsquiz_mathsquiz_step3`.
- **Highest blast radius:** `object` (3), `polygons_polygons_polygon_init` (3), `Polygon` (2).
- **Orphan components:** `mathsquiz_mathsquiz`, `mathsquiz_mathsquiz_step1` (standalone scripts, no call edges).
- **Dependency cycles:** none.

The Architect agent (Opus) returned an **evidence-gated** refactor plan — cheap disconfirmation first (quantify blast radius, try to disprove the SPOF), then an availability fix (redundant path), and decomposition last and only if responsibilities are genuinely mixed. Full text in [`reports/recommendations.md`](reports/recommendations.md).

## Token efficiency (graph-guided vs baseline)

| Metric | Baseline (raw code) | Graph-guided |
|---|---|---|
| Total tokens | 3541 | 932 |
| Files read | 5 | 2 |
| Units read | 460 | 45 |
| Time to root cause (s) | 18.3 | 7.4 |

**Token saving: 73.7%** (≥40% target met). Both runs reached the root cause with tests green; the graph-guided run read 2 curated artifacts instead of all 5 source files. Full table in [`reports/token_efficiency.md`](reports/token_efficiency.md).
