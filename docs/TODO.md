# TODO — ArchAgent Task Board

| | |
|---|---|
| **Document** | Tasks Document (TODO) |
| **Project** | ArchAgent |
| **Version** | 1.00 |
| **Date** | 2026-06-12 |
| **Status** | Active |

Derived from [`PRD.md`](PRD.md) and [`PLAN.md`](PLAN.md); source requirements in
[`assignment_brief.md`](assignment_brief.md).
Status legend: ☐ not started · ◐ in progress · ☑ done.
Priority: P0 (must) · P1 (should) · P2 (nice).

---

## Phase 0 — Documentation & Setup  *(Milestone M0)*

| # | Task | Pri | Owner | Status | Definition of Done |
|---|---|---|---|---|---|
| 0.1 | Write `docs/PRD.md` | P0 | Architect | ☑ | PRD covers goals, KPIs, FR/NFR, scope. |
| 0.2 | Write `docs/PLAN.md` | P0 | Architect | ☑ | C4 + workflow + ADRs + schemas present. |
| 0.3 | Write `docs/TODO.md` | P0 | Architect | ☑ | This board. |
| 0.4 | Dedicated PRD: `PRD_graph_analysis.md` | P0 | Architect | ☑ | Metrics + smell rules specified w/ I/O. |
| 0.5 | Dedicated PRD: `PRD_agent_workflow.md` | P0 | Architect | ☑ | Roles, loop, stop criterion specified. |
| 0.6 | Dedicated PRD: `PRD_token_efficiency.md` | P0 | Architect | ☑ | Baseline vs guided method specified. |
| 0.6b | Dedicated PRD: `PRD_research_questions.md` | P0 | Architect | ☑ | 8 EX04 §4 questions tracked w/ evidence source + surface. |
| 0.7 | Get all docs approved before coding | P0 | Lead | ☑ | Sign-off recorded in [`DOCS_SIGNOFF.md`](DOCS_SIGNOFF.md) (v1.00 baseline, 2026-06-16). |
| 0.8 | `pyproject.toml` (ruff/mypy/coverage/dev deps), `uv.lock`, `.python-version` | P0 | DevOps | ☑ | `uv sync` works; lockfile committed. Runtime deps (Grphify/agents) added per-phase. |
| 0.9 | `.gitignore`, `.env-example`, `config/*.json` (v1.00) | P0 | DevOps | ☑ | `.gitignore` ✅; `.env-example` ✅; `config/{setup,rate_limits,logging_config}.json` v1.00 ✅. |
| 0.10 | Install/verify Grphify + Obsidian locally | P0 | DevOps | ☑ | Tool identified = `graphifyy` (CLI `graphify`); setup notes [`GRAPHIFY_SETUP.md`](GRAPHIFY_SETUP.md) + schema fixture committed. Live `graphify extract` on the chosen repo tracked under 1.6. |

## Phase 1 — Graph Pipeline  *(Milestone M1)*

| # | Task | Pri | Owner | Status | Definition of Done |
|---|---|---|---|---|---|
| 1.1 | `RepoLoader` — clone/load target repo | P0 | Dev | ☑ | `infra/repo_loader.py`: loads URL (shallow clone) or local path; injected runner; 100% tested. |
| 1.2 | `GrphifyRunner` — subprocess wrapper | P0 | Dev | ☑ | `infra/grphify_runner.py`: wraps `graphify extract`, lifts graph.json/report/html into `artifacts/`; injected runner; 100% tested. |
| 1.3 | `models.py` — Node/Edge/GraphModel | P0 | Dev | ☑ | `services/models.py`: frozen dataclasses + StrEnum, self-validating; `node_ids`/`dangling_edges` helpers; 100% tested. |
| 1.4 | `GraphLoader` — parse `graph.json` (defensive) | P0 | Dev | ☑ | `services/graph_loader.py`: skips unknown type/kind + malformed entries, defaults version/optionals; tested vs `tests/fixtures/graph.json`; 100%. |
| 1.5 | `ObsidianSync` — write vault + `index.md` + `hot.md` | P0 | Dev | ☑ | `services/obsidian_sync.py`: writes index/hot + per-node notes with `[[wikilinks]]` (graph-view edges); 100% tested. Visual check in Obsidian app = user step. |
| 1.6 | Pick target repo + record env setup notes | P0 | Lead | ☑ | Picked **`andela/buggy-python`** (justified in README — small, zero-setup, cheap); fallback broken-python noted; recorded in `config/setup.json` + `GRAPHIFY_SETUP.md`. Live clone + `graphify extract` = user step. |

## Phase 2 — Reverse Engineering & Analysis  *(Milestone M2)*

| # | Task | Pri | Owner | Status | Definition of Done |
|---|---|---|---|---|---|
| 2.1 | `MetricsCalculator` — centrality, fan-in/out, proximity | P0 | Dev | ☑ | `services/metrics.py`: fan-in/out, degree centrality, BFS proximity; values match hand-computed fixture; 100%. |
| 2.2 | Cycle detection | P0 | Dev | ☑ | `services/cycles.py`: iterative Tarjan SCC (cycles = SCC>1) + self-loops; detects fixture cycle; 100%. |
| 2.3 | `SmellDetector` — God Node / SPOF / oversized / cyclic | P0 | Dev | ☑ | `services/smells.py` + `findings.py`: 4 smells w/ evidence + severity, config-driven thresholds, ranked; articulation points added to metrics; 100%. |
| 2.4 | `ReverseEngineer` — block diagram + OOP class map | P0 | Dev | ☑ | `services/reverse_engineer.py`: Mermaid module flowchart + OOP classDiagram (inheritance + usage); deterministic; 100%. |
| 2.5 | Parallelise independent metric computations | P1 | Dev | ☑ | `services/parallel.py`: `compute_metrics` runs fan-in/out, centrality, articulation, cycles, self-loops in a thread pool; pure reads of frozen graph = thread-safe; matches sequential + concurrent-caller test; 100%. |

## Phase 3 — Agent Crew  *(Milestone M3)*

| # | Task | Pri | Owner | Status | Definition of Done |
|---|---|---|---|---|---|
| 3.1 | `ApiGatekeeper` — rate limit + queue + retry + log | P0 | Dev | ☑ | `shared/gatekeeper.py`: rate-limit + concurrency cap (overflow queues/blocks or rejects) + exponential-backoff retry + logging; injectable clock/sleep; 100% incl. concurrency tests. |
| 3.2 | Agent roles (Explorer/Analyst/Architect/Refactor/Reporter) | P0 | Dev | ☑ | `agents/roles.py`: abstract `Agent` base (prompt + gatekept call + parse) + 5 single-responsibility subclasses + `build_crew`; 100%. |
| 3.3 | `AgentCrew` orchestration (LangGraph) | P0 | Dev | ☑ | `agents/crew.py`: real LangGraph `StateGraph` explore→analyse→recommend→report; smells detected up front; runs to completion; 100%. |
| 3.4 | `RecommendationReport` generation | P0 | Dev | ☑ | `services/recommendation.py`: `build_report` → ranked, evidence-backed report w/ `to_json`/`to_markdown`; deterministic; 100%. |
| 3.5 | Agents consume graph artifacts (not raw code) | P0 | Dev | ☑ | `agents/guards.py`: raw-source detector enforced in `Agent.run` (raises before any model call); crew prompts verified graph-only; 100%. |

## Phase 4 — Refactor Loop  *(Milestone M4)*

| # | Task | Pri | Owner | Status | Definition of Done |
|---|---|---|---|---|---|
| 4.1 | `RefactorEngine` — apply a recommendation | P1 | Dev | ☑ | `services/refactor.py`: apply `FileEdit`s (modify/create, incl. split-module) with snapshot + one-shot revert; 100%. |
| 4.2 | Re-run Grphify + unit tests each iteration | P0 | Dev | ☑ | `services/verification.py`: `Reverifier.reverify` re-graphs + reloads + runs tests (injectable `TestRunner`, default pytest); 100%. |
| 4.3 | Green-test + improvement gate w/ auto-revert | P0 | Dev | ☑ | `services/gate.py`: `RefactorGate.attempt` keeps a change only if tests green AND target centrality drops ≥ threshold, else reverts (ADR-004); 100%. |
| 4.4 | Stop criterion (max iters / no-improve / budget) | P0 | Dev | ☑ | `agents/loop.py`: `StopCriterion.should_stop` (max-iters/budget/no-improve, config-driven) + `run_loop` guaranteed to terminate; 100%. |

## Phase 5 — Token-Efficiency Study  *(Milestone M5)*

| # | Task | Pri | Owner | Status | Definition of Done |
|---|---|---|---|---|---|
| 5.1 | `EfficiencyMeter` — tokens, files/units read, iterations, time-to-root-cause | P0 | Dev | ☑ | `services/efficiency.py`: accumulates tokens (+USD from config prices), files/units, iterations, time-to-root-cause → `RunRecord` (to_dict); injectable clock; 100%. |
| 5.2 | Baseline run (raw code → LLM) | P0 | Dev | ☐ | All metrics recorded for same task. |
| 5.3 | Graph-guided run (index/hot/graph → LLM) | P0 | Dev | ☐ | All metrics recorded for same task. |
| 5.4 | Comparison report + savings % | P0 | QA | ☐ | `reports/` table covers tokens, files/units, iterations, root-cause speed; honest explanation if no saving. |

## Phase 6 — Reports, Research & README  *(Milestone M6)*

| # | Task | Pri | Owner | Status | Definition of Done |
|---|---|---|---|---|---|
| 6.1 | Before/after report — architecture **+ knowledge-level (Obsidian)** | P0 | QA | ☐ | Screenshots + metric deltas in `reports/`; documents Obsidian pages/links/insights added and how understanding changed *(feeds RQ-1)*. |
| 6.2 | `GRAPH_REPORT.md` curated from Grphify | P0 | QA | ☐ | Committed under `artifacts/`. |
| 6.3 | Results notebook (centrality + token charts) | P1 | QA | ☐ | Bar/heatmap charts; LaTeX where useful. |
| 6.4 | Root-cause write-up of findings | P0 | QA | ☐ | Each finding traced to a structural cause. *(feeds RQ-5)* |
| 6.5 | `README.md` (install, usage, examples, config, license) | P0 | Lead | ◐ | Seed committed (overview + dev commands); needs full §8 sections, screenshots + Obsidian shots. |
| 6.6 | Prompt book (significant prompts log) | P1 | Lead | ☐ | `docs/PROMPT_BOOK.md` with context + outputs. |
| 6.7 | Original extension(s) — ≥1 per major part (FR-17) | P1 | Lead | ☐ | ≥1 original extension/analysis delivered per major part (e.g. orphan-component+auto-docs, blast-radius/impact report, `hot.md` from `git diff`); documented *(feeds RQ-8)*. |
| 6.8 | Answer all 8 research questions (`PRD_research_questions.md`) | P0 | Lead | ☐ | Every RQ has a written answer + pointer; surfaced in README/reports/Obsidian per coverage checklist. |

## Phase 7 — Quality Gates (continuous)  *(applies every phase)*

| # | Task | Pri | Owner | Status | Definition of Done |
|---|---|---|---|---|---|
| 7.0 | CI workflow — quality gates on push/PR (`.github/workflows/ci.yml`) | P0 | DevOps | ☑ | Runs uv sync + ruff + ruff format + mypy + pytest/cov; green on `main`. 150-line & secret-scan steps wired, activate w/ 7.1/7.4. |
| 7.1 | All files ≤ 150 LOC (`scripts/check_line_limit.py`) | P0 | All | ☐ | Script committed; CI 150-line step enforces. |
| 7.2 | `ruff check` = 0 violations | P0 | All | ◐ | Gate wired in CI + passing on current code. |
| 7.3 | Coverage ≥ 85 % | P0 | QA | ◐ | Gate wired (`fail_under=85`); currently 100% on seed. |
| 7.4 | No secrets in code; `.env-example` present (`scripts/secret_scan.py`) | P0 | DevOps | ☐ | `.env` git-ignored ✅; `.env-example` + scan script pending. |
| 7.5 | Version stamps at 1.00 validated at startup | P0 | Dev | ◐ | `version.py` (constant + `parse/is_compatible`) seeded; startup check pending. |
| 7.6 | Public GitHub repo w/ README + clean history | P0 | Lead | ◐ | Repo public + README seeded; deliverables ongoing. |

---

## Critical Path

`0.7 → 0.8/0.10 → 1.2 → 1.4 → 2.3 → 3.3 → 5.4 → 6.1`
(Docs approved → env ready → graph produced → smells found → crew runs → token study → report.)

## Definition of Done (project)

All P0 tasks ☑, every quality gate in Phase 7 green, and the acceptance criteria in
[`PRD.md` §2.3](PRD.md) satisfied on at least one target repository.
