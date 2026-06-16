# PRD — ArchAgent: Token-Efficient Architectural Analysis & Refactoring Agent

| | |
|---|---|
| **Document** | Product Requirements Document (PRD) |
| **Project** | ArchAgent — Reverse Engineering, Debugging & Token-Efficient Agentic AI |
| **Course** | Assignment 04 (L07) — Vibe Coding |
| **Version** | 1.00 |
| **Date** | 2026-06-12 |
| **Status** | Draft — pending approval |

---

## 1. Overview & Context

### 1.1 Summary

**ArchAgent** is a multi-agent AI system that explores an *unfamiliar* Python codebase,
turns it into a **knowledge graph** with **Grphify**, represents that knowledge in an
**Obsidian** vault, and then uses a **CrewAI / LangGraph** agent crew to:

1. **Reverse-engineer** the architecture (OOP class map, module block diagram, data flow).
2. **Detect architectural bugs** — God Nodes, single points of failure, circular
   dependencies, oversized modules, and "Lost in the Middle" context problems.
3. **Recommend and apply refactorings**, re-run Grphify, and **iterate** until a defined
   stop criterion is met — re-running the unit tests after every change so behaviour is
   never broken.
4. **Prove token efficiency** — compare a *baseline* run (feeding raw code to the LLM)
   against a *graph-guided* run (feeding only the distilled `index.md` / `hot.md` /
   `graph.json`), and report the savings.

The deliverable is a professional Python package plus an Obsidian vault, a `GRAPH_REPORT.md`,
a baseline-vs-graph-guided comparison, and before/after architecture evidence.

### 1.2 The User Problem

Engineers regularly inherit large codebases they did not write. Reading them end-to-end is
slow, and feeding the whole repo to an LLM is expensive and degrades quality (the model
loses the relevant detail in a sea of tokens — the *Lost in the Middle* effect). There is no
cheap, repeatable way to (a) understand an unknown system's architecture and (b) get
*actionable, architecture-level* improvement recommendations without burning a large token
budget.

### 1.3 The Idea / Solution

Instead of sending raw source to the model, ArchAgent sends a **compressed structural
representation** of the code (a knowledge graph + curated Markdown indexes). The agent
reasons over structure, not over every line. This is both cheaper (fewer tokens) and more
accurate (the model sees the architecture directly). The same graph also powers an
Obsidian knowledge base a human can browse and converse with.

### 1.4 Target Audience

- **Primary:** Software engineers / architects onboarding onto an unfamiliar repository.
- **Secondary:** Tech leads doing architecture review and technical-debt triage.
- **Tertiary (stretch):** Anyone managing structured systems — e.g. an org chart / RnD-HR
  structure — that can be expressed as a graph (noted as an extensibility direction).

### 1.5 Context / Background Concepts

| Concept | Meaning in this project |
|---|---|
| **Grphify** | Local CLI that parses a Python repo and emits a knowledge graph (`graph.json`), an `index.md`, a `hot.md`, a `GRAPH_REPORT.md`, and an HTML graph view. Runs fully offline. |
| **Obsidian** | Local Markdown knowledge-base app used to *visualise* the graph and ask questions over it. |
| **Knowledge Graph** | Nodes = modules/classes/functions; edges = imports/calls/inheritance. |
| **God Node** | A node with abnormally high centrality — a module everything depends on; a structural risk / single point of failure. |
| **Lost in the Middle** | LLMs under-attend to information in the middle of a long context; avoided here by sending small, curated context instead of whole files. |
| **`index.md`** | Curated entry-point index of the codebase generated from the graph. |
| **`hot.md`** | "Hot" / high-churn or high-centrality nodes worth attention (can be cross-referenced with `git diff`). |

---

## 2. Goals, KPIs & Acceptance Criteria

### 2.1 Measurable Goals

| # | Goal |
|---|---|
| G1 | Generate a complete knowledge graph for at least one target repo and browse it in Obsidian. |
| G2 | Produce an automated reverse-engineering report (block diagram + OOP class map). |
| G3 | Detect ≥ 1 real architectural smell (God Node / SPOF / cycle / oversized module) with evidence. |
| G4 | Run an autonomous analyse → recommend → refactor → re-graph → test loop with a stop criterion. |
| G5 | Demonstrate **measurable token savings** of the graph-guided approach vs. the baseline. |
| G6 | Keep all unit tests green across every refactor iteration. |

### 2.2 KPIs

| KPI | Target |
|---|---|
| Token reduction (graph-guided vs. baseline) on the same task | ≥ 40 % fewer tokens (report actual either way) |
| Architectural issues detected & reported | ≥ 3, each with graph evidence |
| Unit-test pass rate after refactor loop | 100 % (no regressions) |
| Files exceeding 150 LOC | 0 |
| Ruff violations | 0 |
| Global test coverage | ≥ 85 % |
| Mean improvement in target node centrality after refactor | measured & reported (before/after) |

### 2.3 Acceptance Criteria

- [ ] `uv run python -m arch_agent` runs the full pipeline on a configured target repo.
- [ ] Grphify artifacts (`graph.json`, `index.md`, `hot.md`, `GRAPH_REPORT.md`) are produced
      under `artifacts/`.
- [ ] An Obsidian vault under `obsidian/` opens and shows the graph + notes.
- [ ] The agent crew emits ranked, evidence-backed architectural recommendations.
- [ ] The refactor loop applies at least one recommendation, re-graphs, and re-tests.
- [ ] A `reports/` document shows **before vs. after** architecture and **baseline vs.
      graph-guided** token cost.
- [ ] All quality gates pass (ruff = 0, coverage ≥ 85 %, files ≤ 150 LOC, secrets externalised).

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-1 | Fetch / load a target Python repo from a configured GitHub URL or local path. | Must |
| FR-2 | Run Grphify over the repo and persist `graph.json` + Markdown artifacts. | Must |
| FR-3 | Parse `graph.json` into typed in-memory models (nodes, edges, metrics). | Must |
| FR-4 | Generate `index.md` and `hot.md` and sync them into the Obsidian vault. | Must |
| FR-5 | Reverse-engineer an OOP class map and a module block diagram from the graph. | Must |
| FR-6 | Compute structural metrics: centrality, fan-in/fan-out, proximity, cycle detection. | Must |
| FR-7 | Detect architectural smells (God Node, SPOF, oversized module, cyclic deps). | Must |
| FR-8 | Run a multi-agent crew (CrewAI **or** LangGraph) that consumes graph artifacts. | Must |
| FR-9 | Produce ranked, evidence-backed refactoring recommendations. | Must |
| FR-10 | Apply a selected recommendation to the codebase (e.g. split oversized module). | Should |
| FR-11 | Re-run Grphify and unit tests after each change; loop until stop criterion. | Must |
| FR-12 | Enforce a stop criterion (max iterations, no-further-improvement, or budget cap). | Must |
| FR-13 | Run a *baseline* (raw-code) analysis and a *graph-guided* analysis; log token usage. | Must |
| FR-14 | Emit a before/after architecture report and a baseline-vs-graph-guided cost report. | Must |
| FR-15 | Expose every operation through a single **SDK** entry point. | Must |
| FR-16 | Route all LLM/API calls through a centralized **gatekeeper** (rate limit + retry + log). | Must |

### 3.2 Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-1 | **Offline-first** — Grphify and Obsidian run locally; only the LLM calls leave the machine. |
| NFR-2 | **Configuration-driven** — repo URL, model, rate limits, thresholds in `config/*.json`; no hard-coded values. |
| NFR-3 | **Security** — API keys only via env vars; `.env` git-ignored; `.env-example` committed. |
| NFR-4 | **Quality** — files ≤ 150 LOC, ruff = 0 violations, coverage ≥ 85 %, docstrings everywhere. |
| NFR-5 | **Package manager** — `uv` exclusively (no `pip` / `venv` / `python -m`). |
| NFR-6 | **Reproducibility** — `pyproject.toml` + `uv.lock` committed; deterministic artifact paths. |
| NFR-7 | **Cost transparency** — token in/out and $ cost logged per run and summarised. |
| NFR-8 | **Performance** — independent graph/metric computations parallelised where safe. |
| NFR-9 | **Versioning** — code + config versions start at 1.00 and validated at startup. |

### 3.3 User Stories

- **US-1** — *As an engineer*, I point ArchAgent at an unknown repo and get a readable
  architecture overview in Obsidian, so I understand it without reading every file.
- **US-2** — *As an architect*, I receive ranked architectural-smell findings with graph
  evidence, so I know where the structural risk is.
- **US-3** — *As a developer*, the agent applies a refactor and proves my tests still pass,
  so I trust the change.
- **US-4** — *As a budget owner*, I see token cost baseline vs. graph-guided, so I can
  justify the graph-guided approach.

### 3.4 Use-Case Scenarios

1. **Cold onboarding** — clone `andela/buggy-python` → graph → Obsidian → read block diagram.
2. **Architecture audit** — run crew on `martinpeck/broken-python` → get God-Node finding →
   apply split → re-graph → confirm centrality dropped and tests pass.
3. **Cost study** — run the same "summarise architecture" task twice (raw vs. graph-guided) →
   compare token tables.

---

## 4. Assumptions, Dependencies, Constraints & Out-of-Scope

### 4.1 Assumptions

- Grphify and Obsidian are installable and runnable locally on the grader's machine.
- The target repo can be made to run under a `uv` virtual environment (or Docker for BugsInPy).
- An LLM API key is available via environment variable at run time.

### 4.2 Dependencies

| Dependency | Use |
|---|---|
| Grphify (CLI) | Knowledge-graph generation |
| Obsidian (app) | Graph visualisation & note browsing |
| CrewAI **or** LangGraph | Multi-agent orchestration |
| An LLM provider SDK | Reasoning agents (latest Claude model by default) |
| `uv` | Package & task management |
| `pytest`, `pytest-cov`, `ruff` | Quality gates |

### 4.3 Constraints

- The whole project is scoped to be completable by a pair in ~5 focused hours.
- Environment setup must not become a rabbit hole — if a target repo is too hostile to set up,
  fall back to a smaller repo (`andela/buggy-python`).
- We focus on **architectural** bugs, not trivial line-level logic bugs.

### 4.4 Out of Scope

- Production deployment / hosting; cloud servers (everything is local).
- Supporting non-Python codebases.
- A bespoke graph engine — we use Grphify's output, we do not reimplement it.
- A custom GUI — Obsidian is the visualisation surface; our own UI is a CLI.

---

## 5. Timeline & Milestones

| Milestone | Deliverable | Target |
|---|---|---|
| M0 — Docs approved | PRD, PLAN, TODO, dedicated PRDs | Day 0 |
| M1 — Graph pipeline | Grphify wired; `graph.json` + Obsidian vault produced | Day 0 |
| M2 — Reverse engineering | Block diagram + OOP map + metrics + smell detection | Day 1 |
| M3 — Agent crew | CrewAI/LangGraph workflow producing recommendations | Day 1 |
| M4 — Refactor loop | Apply → re-graph → re-test loop with stop criterion | Day 1 |
| M5 — Efficiency study | Baseline vs. graph-guided token report | Day 2 |
| M6 — Reports & README | before/after, GRAPH_REPORT, README, screenshots | Day 2 |

---

## 6. Dedicated PRDs

Per the submission guidelines, each central mechanism gets its own PRD:

- `docs/PRD_graph_analysis.md` — graph parsing, metrics, and smell-detection algorithms.
- `docs/PRD_agent_workflow.md` — the CrewAI/LangGraph crew, roles, and refactor loop.
- `docs/PRD_token_efficiency.md` — baseline vs. graph-guided measurement methodology.

(These are tracked in `docs/TODO.md` and authored before their respective code.)

---

## 7. Success Definition

ArchAgent succeeds if a grader can run one command on an unfamiliar repo and receive:
a browsable Obsidian architecture map, ≥ 3 evidence-backed architectural findings, at least
one applied-and-verified refactor, and a clear table showing the graph-guided approach used
materially fewer tokens than the baseline — all produced by code that passes every quality
gate.
