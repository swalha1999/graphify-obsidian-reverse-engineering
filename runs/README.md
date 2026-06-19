# Runs — per-repository findings

Each subfolder is a self-contained ArchAgent run against one target repository,
so findings for different repos never overwrite each other. The repo root
(`artifacts/`, `obsidian/`, `reports/`) holds the original **`andela/buggy-python`**
submission (the pipeline's default output location); everything here is an additional target.

> **Name clash — don't confuse these two.** **`andela/buggy-python`** (the small teaching
> repo at the repo root) is **not** the same as **`soarsmu/BugsInPy`** (the large
> bug-benchmark framework in [`bugsinpy/`](bugsinpy/)). Different owners, different repos.

| Run | Target | Model | Headline |
|---|---|---|---|
| [`broken-python/`](broken-python/) | [`martinpeck/broken-python`](https://github.com/martinpeck/broken-python) | `claude-opus-4-8` | God Node + SPOF = `Polygon`; 73.7% token saving |
| [`bugsinpy/`](bugsinpy/) | [`soarsmu/BugsInPy`](https://github.com/soarsmu/BugsInPy) | `claude-opus-4-8` | 1633-node bash framework but **flat** (no hubs/cycles); token thesis inverts (−3133%) |

Each run folder contains:

- `artifacts/` — Graphify outputs (`graph.json`, `GRAPH_REPORT.md`, `graph.html`)
- `obsidian/` — the generated knowledge vault (`index.md`, `hot.md`, and `nodes/` for graphs small enough to be useful)
- `reports/` — `architecture.md`, `recommendations.md` / `.json`, `token_efficiency.md`
- `setup.snapshot.json` — the exact config used for the run
- `FINDINGS.md` — a human summary of what the run revealed

## Reproduce a run

```bash
uv tool install graphifyy            # provides the `graphify` CLI
git clone <target-url> data/target   # data/ is git-ignored
# point config/setup.json at the target + model, then run the pipeline:
uv run python -m arch_agent
```
