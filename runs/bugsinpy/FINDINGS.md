# Findings — `soarsmu/BugsInPy` (Opus 4.8)

| | |
|---|---|
| **Target** | [`soarsmu/BugsInPy`](https://github.com/soarsmu/BugsInPy) (`master`) |
| **Model** | `claude-opus-4-8` (Opus 4.8) |
| **Date** | 2026-06-19 |
| **What it is** | A bug-benchmark **framework**: 810 shell scripts + 1 `.py` file (the buggy Python projects — pandas, scrapy, etc. — are *downloaded on demand*, not stored). Graphify graphs the **bash framework** via `tree-sitter-bash`. |

## How it was run

1. `graphify extract` over a code-only stage (810 `.sh` + 1 `.py`) → AST graph.
2. `graphify cluster-only --backend claude --model claude-opus-4-8`.
3. ArchAgent pipeline (smells → crew → token study) over the graph, with `claude-opus-4-8`.

> Community naming again fell back to `Community N` (the `graphifyy[anthropic]` extra is absent from graphify's isolated tool env). The 1633-node obsidian vault and the 2501-line reverse-engineered mega-diagram were **pruned** from this folder — at this scale they are noise, not signal (that is itself a finding). Both are reproducible from `artifacts/graph.json`.

## Graph

- **Graphify / ArchAgent loader:** **1633 nodes · 833 edges · 811 communities** (1621 "modules" = shell scripts, 12 functions; all edges are calls). This is by far the largest target — ~100× broken-python.

## The headline: big but **flat**

Despite the size, the graph has almost no coupling:

- **Max degree centrality: 0.001** — no node is central. No God Nodes.
- **Max fan-in: 2** — no node is a hub. No SPOFs.
- **Articulation points: 0** · **Dependency cycles: 0**.
- Smell detector returns **0 smells** at any reasonable threshold.

BugsInPy is an **archipelago**: ~500 near-identical, independent per-bug `bug_patch.sh` / `run_test.sh` / `*_verify.sh` scripts that share no structure. There is no architecture to reverse-engineer — only repetition. The Architect agent (Opus) correctly **refused to invent refactors** and instead recommended validating scan coverage and detector calibration (a clean result on a structureless corpus is exactly when false confidence is the risk). See [`reports/recommendations.md`](reports/recommendations.md).

## The token thesis **inverts** here

| Metric | Baseline (raw code) | Graph-guided |
|---|---|---|
| Total tokens | 1415 | 45742 |
| Files read | 1 | 2 |

**Token "saving": −3133%** — graph-guidance cost ~32× *more*. Why: BugsInPy's Python surface is a single 29-line file, so the raw baseline is tiny, while the curated graph index for 1633 nodes is ~45k tokens. The graph-guided approach pays off when the codebase is large *code*; here the code is one file and the bulk is a sprawling shell framework, so curating the graph is pure overhead. Reported honestly per the brief — see [`reports/token_efficiency.md`](reports/token_efficiency.md).

## Takeaway

A useful contrast to [`../broken-python`](../broken-python/) (small, coupled, 73.7% saving): target **shape** matters more than raw size. A large but flat, repetitive corpus produces a big graph with no structural signal and negative token economics. To study *real* bugs with BugsInPy you must first materialize one project (`bugsinpy-checkout`) and graph *that* — a separate, much heavier run.
