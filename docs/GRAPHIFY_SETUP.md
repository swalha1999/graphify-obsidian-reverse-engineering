# Grphify (Graphify) — Setup & Usage Notes

| | |
|---|---|
| **Document** | Environment setup notes — Grphify |
| **Project** | ArchAgent |
| **Version** | 1.00 |
| **Date** | 2026-06-16 |
| **Status** | Install/run pending (see §5) |

Supports [`TODO.md`](TODO.md) tasks **0.10** (install/verify Grphify) and **1.6** (env notes).
The `GrphifyRunner` (TODO 1.2) wraps the CLI documented here as a subprocess (ADR-003).

---

## 1. What "Grphify" is

The assignment's **Grphify** is the open-source tool **Graphify** by Safi Shamsi
(`safishamsi`). It turns a folder of code/docs into a queryable **knowledge graph**, doing the
expensive analysis once and answering later queries by traversing the graph instead of
re-reading raw files — exactly the token-efficiency thesis of this assignment.

| | |
|---|---|
| **PyPI package** | `graphifyy` (double-`y`; `graphify` was already taken) |
| **CLI command** | `graphify` |
| **Source** | https://github.com/safishamsi/graphify |
| **PyPI** | https://pypi.org/project/graphifyy/ |
| **License / Python** | MIT · Python ≥ 3.10 |

> ⚠️ **Name caveat:** install the package **`graphifyy`**, but invoke the command **`graphify`**.

---

## 2. Install

Recommended (isolated tool install):

```bash
uv tool install graphifyy
```

Alternatives: `pipx install graphifyy` or `pip install graphifyy`.

Verify (no API key needed):

```bash
graphify --help
```

---

## 3. Generate the graph (headless)

```bash
graphify extract <path-to-target-repo>
```

- **Requires an LLM API key** (e.g. `ANTHROPIC_API_KEY`) and **consumes tokens** — this is a
  paid call. Keep keys in `.env` (git-ignored, PRD NFR-3), never committed.
- Outputs land in **`graphify-out/`**:
  - `graph.json` — the queryable knowledge graph (our primary input)
  - `GRAPH_REPORT.md` — key concepts + suggested questions
  - `graph.html` — interactive browser visualization
- Optional exports include an **Obsidian vault** and callflow diagrams — that vault feeds our
  `obsidian/` deliverable.

Query/traverse (optional, also paid):

```bash
graphify query "what does module X depend on?"
graphify path "EntityA" "EntityB"
```

---

## 4. How ArchAgent consumes it

`GrphifyRunner` invokes `graphify extract` as a subprocess and reads the files from
`graphify-out/`; `GraphLoader` (TODO 1.4) parses `graph.json` **defensively** into the typed
models (`PLAN.md` §3.1). Because of ADR-003 we depend only on these file outputs, so the rest of
the system is testable against the fixture in [`tests/fixtures/graph.json`](../tests/fixtures/graph.json)
without a live (paid) run.

---

## 5. Chosen target repo & status

**Target repo (TODO 1.6):** [`andela/buggy-python`](https://github.com/andela/buggy-python) —
small, self-contained buggy Python scripts; clones and runs with no per-bug environment.
Justification in the [README](../README.md#target-repository).
**Fallback:** [`martinpeck/broken-python`](https://github.com/martinpeck/broken-python) for a
slightly richer target if wanted.

Clone the repo into `data/target` (git-ignored), then run Grphify on it:

```bash
git clone https://github.com/andela/buggy-python data/target
# then run graphify on the working copy:
graphify extract data/target
```

- ✅ Tool identified and verified on PyPI (MIT, by `safishamsi`).
- ✅ Setup notes + schema fixture committed (Phase 1–2 unblocked).
- ✅ Target repo chosen (`andela/buggy-python`) + recorded in `config/setup.json` and the README.
- ⏳ **Pending (your machine, paid):** `uv tool install graphifyy`; clone the repo into
  `data/target`; `graphify extract data/target` → capture a **real** `graph.json` under
  `artifacts/`; note any setup quirks here.

> The agent-driven auto-install was blocked by a safety guard (web-inferred package name); run the
> install command yourself or add a permission rule for it.
