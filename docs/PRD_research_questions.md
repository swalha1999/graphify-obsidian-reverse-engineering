# PRD — Research Questions (Answer Tracker)

| | |
|---|---|
| **Document** | Dedicated PRD — Research Questions |
| **Project** | ArchAgent |
| **Version** | 1.00 |
| **Date** | 2026-06-16 |
| **Status** | Active — answers filled in as phases complete |

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
- **Surfaced in:** README "Architecture overview"; `reports/` before/after; Obsidian `index.md`.
- **Status:** ☐
- **Answer:** _TBD_

### RQ-2 — Most central elements
> Which **components / modules / classes / functions** are the **most central** in the system?

- **Evidence from:** MetricsCalculator (centrality, fan-in/out). *(TODO 2.1)*
- **Surfaced in:** README; Obsidian `hot.md`; `GRAPH_REPORT.md`.
- **Status:** ☐
- **Answer:** _TBD_

### RQ-3 — Complexity hotspots / God Nodes
> Where are the **complexity hotspots, mixed-responsibility areas, or God Nodes**?

- **Evidence from:** SmellDetector (God Node / SPOF / oversized / cyclic). *(TODO 2.3)*
- **Surfaced in:** README; `reports/` findings; Obsidian `hot.md`.
- **Status:** ☐
- **Answer:** _TBD_

### RQ-4 — Extracting block + OOP schema without docs
> How can you extract an **architectural block diagram** and an **OOP schema** from the code
> even when the **original documentation is partial or missing**?

- **Evidence from:** ReverseEngineer methodology (graph → Mermaid/Markdown). *(TODO 2.4)*
- **Surfaced in:** README "How reverse engineering was done"; `reports/`.
- **Status:** ☐
- **Answer:** _TBD_

### RQ-5 — Bug identification & root cause
> How did you **identify the bug**, what was the **root cause**, and what **steps** led you to it?

- **Evidence from:** Root-cause write-up; refactor loop trace. *(TODO 6.4)*
- **Surfaced in:** README "Bug & root cause"; `reports/` root-cause doc.
- **Status:** ☐
- **Answer:** _TBD_

### RQ-6 — Graph/Obsidian navigation vs. linear reading
> What was the **advantage of the graph representation + Obsidian navigation** compared to
> **linear reading** of files?

- **Evidence from:** Obsidian vault usage; token-efficiency study qualitative notes.
- **Surfaced in:** README; `reports/`; Obsidian note.
- **Status:** ☐
- **Answer:** _TBD_

### RQ-7 — Token savings / fewer code reads
> How did using a **graph-guided AI agent** save tokens or reduce **unnecessary code reads**?

- **Evidence from:** EfficiencyMeter (baseline vs graph-guided). *(TODO 5.1–5.4)*
- **Surfaced in:** README "Token efficiency"; `reports/` comparison table; results notebook.
- **Status:** ☐
- **Answer:** _TBD_

### RQ-8 — Future improvements & extensions
> What **improvements, extensions, or additional agent mechanisms** would you add next?

- **Evidence from:** Creativity / extensibility section. *(TODO 6.7)*
- **Surfaced in:** README "Future work / extensibility".
- **Status:** ☐
- **Answer:** _TBD_

---

## 3. Coverage Checklist (for final submission)

The grader should be able to find every answer in **all three** surfaces where applicable:

| Question | README | reports/ | Obsidian |
|---|---|---|---|
| RQ-1 | ☐ | ☐ | ☐ |
| RQ-2 | ☐ | ☐ | ☐ |
| RQ-3 | ☐ | ☐ | ☐ |
| RQ-4 | ☐ | ☐ | — |
| RQ-5 | ☐ | ☐ | — |
| RQ-6 | ☐ | ☐ | ☐ |
| RQ-7 | ☐ | ☐ | — |
| RQ-8 | ☐ | — | — |
