# Extensions

Original analyses beyond the assignment minimum — **at least one per major part**
(FR-17, `docs/PRD.md`). Each is implemented, tested, and run on the real
`andela/buggy-python` target. Together they feed research question **RQ-8**
([`docs/PRD_research_questions.md`](PRD_research_questions.md)).

| # | Major part | Extension | Where |
|---|---|---|---|
| 1 | Graph analysis / reverse-engineering | **Blast-radius & orphan-component analysis** | [`services/impact.py`](../src/arch_agent/services/impact.py) |
| 2 | Agent workflow | **Parallel metric execution** (thread pool over a frozen graph) | [`services/parallel.py`](../src/arch_agent/services/parallel.py) |
| 3 | Token efficiency / knowledge surface | **`hot.md` risk surface** (rank nodes by fan-in into one curated note) | [`services/obsidian_sync.py`](../src/arch_agent/services/obsidian_sync.py) |

---

## 1. Blast-radius & orphan-component analysis (new in this phase)

`ImpactAnalyzer` adds two original structural analyses on top of the required smell
set, both pure deterministic functions of the graph:

- **Blast radius** of a node `n` = the set of nodes that **transitively depend on** `n`
  (reverse reachability over directed edges, `src` depends on `dst`). It answers *"if
  `n` breaks, what is impacted?"* — a sharper risk signal than raw fan-in, because it
  counts **indirect** dependents, not just immediate ones.
- **Orphan components** = nodes with zero fan-in **and** zero fan-out (isolated): dead-ish
  code or missing wiring worth flagging (the assignment's suggested example, `assignment_brief.md`).

### Result on `andela/buggy-python` (11 nodes, 9 edges)

| Node | Blast radius (transitive dependents) |
|---|---|
| **`snippets_foobar_foo`** | **3** |
| `snippets_foobar` | 1 |
| `snippets_io_average_paid_loans` | 1 |
| `snippets_io_calculate_paid_loans` | 1 |
| `snippets_io_calculate_unpaid_loans` | 1 |
| (others) | 0 |

Orphan components: **none** — every node is wired into the dependency graph.

**Why this matters.** The single highest-impact node is `snippets_foobar_foo` — *the exact
node that is also the SPOF/articulation point and the home of the mutable-default-argument
bug* ([`reports/root_cause.md`](../reports/root_cause.md)). Three independent lenses
(centrality, articulation-point, blast-radius) converge on the same node. That convergence
is the extension's payoff: it gives a quantified *"fix this first"* ordering that fan-in
alone does not.

Covered by [`tests/test_impact.py`](../tests/test_impact.py) (chain, cycle, dangling-edge,
ordering, orphan cases); the suite stays at 100% coverage.

## 2. Parallel metric execution

`parallel.py` runs the independent metric computations (fan-in/out, centrality,
articulation points, cycles) concurrently over the **frozen** `GraphModel`. Because every
task is a pure read with no shared mutable state, the parallel result is bit-for-bit
identical to the sequential one — speed without a correctness risk (NFR-8). This is an
agent-workflow extension: it lets the crew's *analyse* stage scale to larger graphs without
changing any agent logic.

## 3. `hot.md` risk surface

`ObsidianSync` emits a curated **`hot.md`** that ranks nodes by fan-in and links each with
`[[wikilinks]]`. Instead of the agent scanning the whole vault, the *one* hot note is the
high-signal entry point — the knowledge-surface analogue of the token-efficiency thesis:
**curate, don't dump.** It is what lets the Explorer reason from `index.md` + `hot.md`
alone (never raw source), which is what produces the measured 50.3% token saving.

---

## Feeding RQ-8

RQ-8 asks what to build next. These three are the concrete, already-prototyped answers:
the blast-radius analysis generalises to a **change-impact / suspect-ranking** tool
(combine blast radius with `proximity` to failing tests), parallel execution generalises to
a **process-pool** path for large repos, and the `hot.md` surface generalises to a
**`git diff`-driven** hot set (recently-changed × high-fan-in) for review triage.
