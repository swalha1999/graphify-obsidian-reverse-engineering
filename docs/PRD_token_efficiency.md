# Dedicated PRD — Token Efficiency (Baseline vs. Graph-Guided)

| | |
|---|---|
| **Document** | Dedicated PRD — Token Efficiency |
| **Project** | ArchAgent |
| **Version** | 1.00 |
| **Date** | 2026-06-16 |
| **Status** | Draft — pending approval |

Companion to [`PRD.md`](PRD.md) (FR-13, FR-14, §2.2 KPIs) and [`PLAN.md`](PLAN.md)
(§3.3 token-efficiency record). Specifies the **measurement methodology** that proves the
graph-guided approach uses materially fewer resources than feeding raw code to the LLM —
enough to build `services/efficiency.py` (`EfficiencyMeter`, TODO 5.1) and the comparison
report (TODO 5.4) test-first.

---

## 1. Purpose & Scope

Measure and compare **one bug-investigation-and-fix task**, run two ways, and report the
difference. This is the assignment's core thesis (assignment §5.5; avoiding *Lost in the Middle*).

- **In scope:** what the task is, the two modes, the exact metrics captured, where the numbers
  come from, the record/report contract, and honest-reporting rules.
- **Out of scope:** the agent internals (`PRD_agent_workflow.md`) and the metric/smell algorithms
  (`PRD_graph_analysis.md`). This PRD *measures*; it does not change behaviour.

> **Not measured:** the tokens spent *building* ArchAgent, and the per-task development work on
> the TODO board. Only the agent's own LLM usage during the one debugging task is measured.

---

## 2. The Task (held identical across modes)

A single, fixed task on the chosen target repo — e.g. *"locate the root cause of bug X and
propose the fix."* The **same task, same model, same target** is used for both runs so the only
variable is *what context the agent reads*. The task and its seed are pinned in
`config/setup.json` for reproducibility.

---

## 3. The Two Modes

| Mode | What the agent reads | How |
|---|---|---|
| **Baseline (naive)** | raw source files dumped into the prompt, with little focus | bypass the graph; feed whole files |
| **Graph-guided** | `graph.json`, `index.md`, `hot.md`, Obsidian notes; source fetched **lazily** only when refactoring | the normal ArchAgent path (ADR-001) |

Both modes route every call through the **gatekeeper** (FR-16), so token accounting is identical
and fair. The baseline is a deliberately honest "what most people do" control.

---

## 4. Metrics Captured (per run)

Per assignment §5.5, the comparison reports **more than tokens**. For each run the
`EfficiencyMeter` records:

| Metric | Source |
|---|---|
| **Input / output tokens** (+ USD cost) | each LLM response's `usage` object, summed by the gatekeeper |
| **Files / textual units read** | count of files/chunks placed into prompts |
| **Iterations / investigation rounds** | loop counter from the agent workflow |
| **Time / quality to reach root cause & fix** | wall-clock and/or rounds-to-root-cause; whether the fix passed tests |

USD is derived from tokens via per-model rates in config (no hard-coded prices, NFR-2).

---

## 5. Record & Report Contract

### 5.1 Efficiency record (produced — extends `PLAN.md` §3.3)

```jsonc
{
  "task": "find_root_cause_and_fix_bug_x",
  "model": "claude-...",
  "baseline": {
    "in_tokens": 184320, "out_tokens": 2100, "usd": 0.94,
    "files_read": 47, "units_read": 210, "iterations": 6,
    "time_to_root_cause_s": 612, "root_cause_found": true, "tests_green": true
  },
  "graph_guided": {
    "in_tokens": 41210, "out_tokens": 1980, "usd": 0.22,
    "files_read": 4, "units_read": 23, "iterations": 2,
    "time_to_root_cause_s": 143, "root_cause_found": true, "tests_green": true
  },
  "savings_pct": 76.6                       // token reduction; KPI target >= 40%
}
```

### 5.2 Comparison report (TODO 5.4)

A `reports/` Markdown table covering **all** metrics in §4 side by side, plus `savings_pct` and a
short narrative. The results notebook (TODO 6.3) charts tokens and the other dimensions.

---

## 6. KPIs & Honest Reporting

- **KPI:** ≥ 40 % token reduction (PRD §2.2). Report the actual number either way.
- **Honesty rule (assignment + PLAN risk):** if savings are small or negative, report it and
  explain *why* (e.g. agent chatter overhead, a target too small to benefit). A truthful
  before/after beats an inflated claim — measurement integrity is graded, not just the headline %.

---

## 7. Method, Determinism & Edge Cases

- **Fair comparison:** identical task/model/target/seed; same gatekeeper; temperature pinned low
  so runs are reproducible.
- **Isolation:** each mode runs from the same clean repo state; the baseline does not benefit from
  graph artifacts and the graph-guided run does not pre-load raw files.
- **Edge cases:** if the baseline cannot reach the root cause within the token budget, record
  `root_cause_found: false` (that *is* a result); if a provider call fails, the gatekeeper's
  retry/queue keeps accounting consistent; division-by-zero guarded when baseline tokens are 0.

---

## 8. Testing (TDD, NFR-4)

- **Mock the gatekeeper** to return canned `usage` payloads; assert the `EfficiencyMeter` sums
  tokens/files/iterations correctly and computes `savings_pct` (incl. the negative-savings and
  zero-baseline cases).
- Assert the report contract contains every §4 metric for both modes. Coverage ≥ 85 %.

---

## 9. Traceability

| This PRD | Satisfies |
|---|---|
| §3 two modes | PRD **FR-13**; ADR-001; TODO **5.2**, **5.3** |
| §4 metrics + §5.1 record | PRD **FR-13**; `PLAN.md` §3.3; TODO **5.1** |
| §5.2 report | PRD **FR-14**; TODO **5.4**; charts TODO **6.3** |
| §6 KPI / honesty | PRD **§2.2 KPIs**; feeds research question **RQ-7** (`PRD_research_questions.md`) |
