# Before / After — Architecture & Knowledge Level

Target: **[`andela/buggy-python`](https://github.com/andela/buggy-python)** · model `claude-sonnet-4-6`.
Supports assignment §5.4 and TODO 6.1; feeds research question **RQ-1**.

This documents what we understood about the system **before** the graph, and what
changed **after** running ArchAgent — at both the *code/architecture* level and the
*knowledge* level (the Obsidian vault).

---

## 1. Architecture: before vs after

### Before (first glance)
A flat checkout: `main.py` plus four files under `snippets/` (`io.py`, `foobar.py`,
`loop.py`, `__init__.py`). From the directory listing alone there is **no signal**
about which parts are central, how the pieces depend on each other, or where the
structural risk sits. One would guess they are independent exercise snippets.

### After (graph-derived, `artifacts/graph.json` — 11 nodes, 9 edges)
Grphify's AST extraction + our metrics revealed structure the directory hid:

| Insight | Evidence |
|---|---|
| **`snippets_io` is the hub** — the I/O module everything routes through | centrality **0.40**, fan-out **4** (its four functions `read_file` / `calculate_unpaid_loans` / `calculate_paid_loans` / `average_paid_loans`) |
| **`snippets_foobar_foo` is a single point of failure** | **articulation point**, fan-in **3** — removing it disconnects part of the graph |
| No dependency cycles | Tarjan SCC found none |

→ 3 evidence-backed findings (2 God-Node candidates + 1 SPOF), ranked in
[`reports/recommendations.md`](recommendations.md). The block diagram + OOP map are
in [`reports/architecture.md`](architecture.md).

**What wasn't obvious at first glance (RQ-1):** that a tiny repo still has a clear
*hub-and-spoke* shape — the I/O layer is the coupling point, and one function is a
topological bottleneck. That is exactly where a change is riskiest.

---

## 2. Knowledge level: the Obsidian vault, before vs after

### Before
No knowledge base — only source files.

### After (`obsidian/`)
ArchAgent wrote a browsable vault:

- **`index.md`** — entry point: node/edge counts and every node grouped by type, each a `[[wikilink]]`.
- **`hot.md`** — the high-fan-in nodes worth attention first.
- **`nodes/*.md`** — one note per node (12 notes), each linking to what it *depends on* and what *depends on it*, so Obsidian's graph view renders the dependency structure.

**How understanding changed:** the vault turns "five files" into a navigable map
where the hub (`snippets_io`) and the bottleneck (`snippets_foobar_foo`) are one
click apart and visually central in the graph view — the same insight the metrics
quantified, now explorable by a human.

---

## 3. Code level: the bug fix (before/after)

The structural analysis pointed at the most-depended-on module, `snippets/io.py`,
which is where the real defects live (see [`reports/root_cause.md`](root_cause.md) for
the full trace). In brief, the before/after of the code:

| | Before (buggy) | After (fixed) |
|---|---|---|
| dict access | `data("loans")`, `loan.amount` | `data["loans"]`, `loan["amount"]` |
| operator | `status !== "unpaid"` (JS) | `status != "unpaid"` |
| builtin | `sun(unpaid_loans)` (typo) | `sum(unpaid_loans)` |

The graph made `snippets_io`'s centrality explicit *before* reading a line of its
source — which is the point: structure first, raw code only when warranted.

---

## 4. Screenshots

The Obsidian graph view and vault are reproducible locally: open the `obsidian/`
folder as a vault in Obsidian. (Run on the grader's machine; the committed Markdown
under `obsidian/` is the same content the graph view renders.)
