# PRD — Research Questions (Answer Tracker)

| | |
|---|---|
| **Document** | Dedicated PRD — Research Questions |
| **Project** | ArchAgent |
| **Version** | 1.00 |
| **Date** | 2026-06-16 |
| **Status** | Complete — all 8 questions answered & surfaced |

Companion to [`PRD.md`](PRD.md), [`PLAN.md`](PLAN.md), and [`TODO.md`](TODO.md).

---

## 1. Purpose

The assignment (EX04 §4, *Research Questions / שאלות מחקר והבנה*) defines **8 questions**
that are *part of the deliverable itself*. Per the brief, the answers **must be expressed
in the README, in the reports, and in the Obsidian pages** — not just held in our heads.

Unlike the other dedicated PRDs (`PRD_graph_analysis`, `PRD_agent_workflow`,
`PRD_token_efficiency`), this document does **not** specify a code mechanism. It is an
**answer tracker**: each question is mapped to (a) the phase/artifact that produces its
evidence and (b) the final answer, which is filled in as the work progresses.

**Definition of done:** every question below has a written answer *and* a pointer to where
that answer is surfaced for the grader (README section / report file / Obsidian note).

---

## 2. The Questions, Evidence Sources & Answer Status

Status legend: ☐ unanswered · ◐ partial · ☑ answered & surfaced.

### RQ-1 — Actual architecture & surprises
> What is the project's **actual architecture**, and what did you discover about it that
> was **not obvious at first glance**?

- **Evidence from:** ReverseEngineer (block diagram + OOP map), GraphLoader. *(TODO 2.4)*
- **Surfaced in:** README "Architecture"; [`reports/before_after.md`](../reports/before_after.md), [`reports/architecture.md`](../reports/architecture.md); Obsidian [`index.md`](../obsidian/index.md).
- **Status:** ☑
- **Answer:** The target (`andela/buggy-python`) is an 11-node, 9-edge dependency graph: a thin
  `foobar` demo path plus a small **loan-calculation domain** layered on an I/O module. The
  flat file list hides two things the graph made obvious: (1) **`snippets_io` is a coupling
  hub** — every calculation function (`calculate_paid_loans`, `calculate_unpaid_loans`,
  `average_paid_loans`) routes through it (fan-out 4, centrality 0.40), so I/O and logic are
  not separated; and (2) the tiny helper `foo()` is structurally load-bearing — an
  **articulation point** whose removal disconnects the graph. Neither is visible by reading
  file names; both fall out of the extracted graph immediately.

### RQ-2 — Most central elements
> Which **components / modules / classes / functions** are the **most central** in the system?

- **Evidence from:** MetricsCalculator (centrality, fan-in/out). *(TODO 2.1)*
- **Surfaced in:** README "What the analysis found"; Obsidian [`hot.md`](../obsidian/hot.md); [`artifacts/GRAPH_REPORT.md`](../artifacts/GRAPH_REPORT.md).
- **Status:** ☑
- **Answer:** Two nodes dominate. **`snippets_io`** is the most central by degree
  (centrality **0.40**, fan-out 4) — the I/O layer everything depends on.
  **`snippets_foobar_foo`** is next (centrality **0.30**, fan-in 3) and is the most central
  by *impact*: its blast radius (transitive dependents) is **3**, the largest in the graph
  ([`docs/EXTENSIONS.md`](EXTENSIONS.md)). Centrality and blast-radius agree on these two as
  the system's load-bearing elements.

### RQ-3 — Complexity hotspots / God Nodes
> Where are the **complexity hotspots, mixed-responsibility areas, or God Nodes**?

- **Evidence from:** SmellDetector (God Node / SPOF / oversized / cyclic). *(TODO 2.3)*
- **Surfaced in:** README; [`reports/recommendations.md`](../reports/recommendations.md); Obsidian [`hot.md`](../obsidian/hot.md).
- **Status:** ☑
- **Answer:** Three findings. **God Node `snippets_io`** — the mixed-responsibility hotspot:
  it mixes file reading with computation, so every calculator depends on it. **God Node +
  SPOF `snippets_foobar_foo`** — both over-depended-on *and* an articulation point. No
  oversized or cyclic smells in this small repo. The hotspot is unambiguously the I/O hub
  plus the `foo()` choke point; both are the recommended decomposition targets.

### RQ-4 — Extracting block + OOP schema without docs
> How can you extract an **architectural block diagram** and an **OOP schema** from the code
> even when the **original documentation is partial or missing**?

- **Evidence from:** ReverseEngineer methodology (graph → Mermaid/Markdown). *(TODO 2.4)*
- **Surfaced in:** README "Reverse-engineering process"; [`reports/architecture.md`](../reports/architecture.md).
- **Status:** ☑
- **Answer:** Bottom-up from the code itself, no docs required: (1) **Grphify** parses the
  AST into a `graph.json` (modules/classes/functions as nodes, imports/calls/inherits as
  edges); (2) the `graphify_adapter` normalises that node-link JSON into typed models; (3)
  `MetricsCalculator` + `cycles.py` derive structure (fan-in/out, centrality, articulation
  points, SCCs); (4) `ReverseEngineer` renders that to a **Mermaid block diagram + OOP class
  map** in [`reports/architecture.md`](../reports/architecture.md). Documentation is an
  *output*, regenerated deterministically from the graph — so partial/missing original docs
  are irrelevant.

### RQ-5 — Bug identification & root cause
> How did you **identify the bug**, what was the **root cause**, and what **steps** led you to it?

- **Evidence from:** Root-cause write-up; refactor loop trace. *(TODO 6.4)*
- **Surfaced in:** README "Bug, root cause & fix"; [`reports/root_cause.md`](../reports/root_cause.md).
- **Status:** ☑
- **Answer:** We did **not** read every file. The metrics/smells ranked
  `snippets_foobar_foo` as both a God Node and a SPOF, so we opened *that node first* and
  found `def foo(bar=[])`. **Root cause:** Python evaluates default arguments **once at
  definition time**, so the single `[]` is shared across calls and `append` accumulates
  (`["baz"]`, `["baz","baz"]`, …). **Fix:** `bar=None` + `if bar is None: bar = []`. The hub
  `snippets_io` additionally carries line-level bugs (`data("loans")`, `!==`, `sun`/`length`
  typos) — consistent with it being the structural risk centre. Full trace in
  [`reports/root_cause.md`](../reports/root_cause.md).

### RQ-6 — Graph/Obsidian navigation vs. linear reading
> What was the **advantage of the graph representation + Obsidian navigation** compared to
> **linear reading** of files?

- **Evidence from:** Obsidian vault usage; token-efficiency study qualitative notes.
- **Surfaced in:** README "How Grphify & Obsidian are used"; [`reports/token_efficiency.md`](../reports/token_efficiency.md); Obsidian [`hot.md`](../obsidian/hot.md).
- **Status:** ☑
- **Answer:** Linear reading forces you through every file in arbitrary order with no signal
  about what matters. The graph + Obsidian vault inverts that: **`hot.md`** ranks nodes by
  fan-in so the highest-risk node is the *first* thing you see, and `[[wikilinked]]` notes
  let you traverse *dependencies* instead of directory listings. Concretely, the guided run
  read **2 files / 35 units** versus the baseline's **5 files / 116 units** to reach the same
  root cause — ~3× fewer code reads — because the structure told us where to look.

### RQ-7 — Token savings / fewer code reads
> How did using a **graph-guided AI agent** save tokens or reduce **unnecessary code reads**?

- **Evidence from:** EfficiencyMeter (baseline vs graph-guided). *(TODO 5.1–5.4)*
- **Surfaced in:** README "Before / after & token efficiency"; [`reports/token_efficiency.md`](../reports/token_efficiency.md); [`notebooks/results.ipynb`](../notebooks/results.ipynb).
- **Status:** ☑
- **Answer:** By sending the model a compact **graph + curated notes** instead of dumping
  raw source. Same task, two contexts (`services/study.py`): the baseline used **2,588 total
  tokens** (746 in / 1,842 out, 5 files) and the graph-guided run used **1,286** (308 in /
  978 out, 2 files) — a **50.3% reduction**, above the 40% target, while both reached the bug
  with tests green. Fewer input tokens *and* fewer/shorter outputs, because the model reasons
  over ~2.4× less input and isn't lost in the middle of irrelevant files.

### RQ-8 — Future improvements & extensions
> What **improvements, extensions, or additional agent mechanisms** would you add next?

- **Evidence from:** Creativity / extensibility section. *(TODO 6.7)*
- **Surfaced in:** README "Extensions"; [`docs/EXTENSIONS.md`](EXTENSIONS.md).
- **Status:** ☑
- **Answer:** Three are already prototyped (see [`docs/EXTENSIONS.md`](EXTENSIONS.md)):
  **blast-radius / orphan analysis** (`services/impact.py`), **parallel metric execution**,
  and the **`hot.md` risk surface**. Next steps generalise these: (1) a **change-impact /
  suspect-ranking** tool combining blast radius with `proximity` to failing tests; (2) a
  **`git diff`-driven hot set** (recently-changed × high-fan-in) for review triage; (3) a
  **process-pool** path so the analysis scales to large repos; and (4) auto-generated docs
  for detected orphan components.

---

## 3. Coverage Checklist (for final submission)

The grader should be able to find every answer in **all three** surfaces where applicable:

| Question | README | reports/ | Obsidian |
|---|---|---|---|
| RQ-1 | ☑ | ☑ | ☑ |
| RQ-2 | ☑ | ☑ | ☑ |
| RQ-3 | ☑ | ☑ | ☑ |
| RQ-4 | ☑ | ☑ | — |
| RQ-5 | ☑ | ☑ | — |
| RQ-6 | ☑ | ☑ | ☑ |
| RQ-7 | ☑ | ☑ | — |
| RQ-8 | ☑ | — | — |
