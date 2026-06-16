# PRD — Graph-Guided Reverse Engineering & Token-Efficient Agentic Debugging

**Project:** Reverse Engineering, Debugging and Token-Efficient Agentic AI with Grphify and Obsidian
**Source assignment:** EX04 (Lesson L07), Dr. Yoram Segal — June 2026, v1.0
**Repo:** https://github.com/swalha1999/graphify-obsidian-reverse-engineering
**Team:** swalha1999 + Mhmdabad (pairs, submitted as a Python project on GitHub)

---

## 1. Summary

Take an **unfamiliar** Python codebase containing real bugs, reverse-engineer it, and represent
its structure and our findings as a **knowledge graph** (via **Grphify**) inside an **Obsidian**
vault. Then build an **AI agent** (CrewAI or LangGraph) that debugs **graph-first** — reasoning
over the graph and Obsidian notes before ever reading raw source — to find and fix a bug while
**spending dramatically fewer tokens** than naive whole-file reading.

The deliverable is not "fix a bug." It is a demonstration of *how* we research an unknown system,
*how* we document it, *how* we drive an AI agent as an engineering tool, and *proof* that
graph-guided context is more efficient than raw code reading.

### Guiding principle ("Lost in the Middle")
Based on the lecture: LLMs degrade with long context windows; relevant facts buried mid-context
get lost. The answer is not bigger context — it is **structured, navigable knowledge** (a graph +
focused notes) so the agent reads little and reasons well.

---

## 2. Goals & Non-Goals

### Goals
- Perform a **systematic** investigation of a system we don't already know.
- Build a **graph representation** of the codebase and understand the *actual* (vs. assumed) architecture.
- Formulate and answer explicit **research questions**.
- Run an **AI agent** that operates token-efficiently in a controlled, measured way.
- **Find, root-cause, and fix** one real bug.
- Show the change at **both** the code level and the knowledge/documentation level.
- **Prove** token savings: naive baseline vs. graph-guided.

### Non-Goals
- Not a mechanical execution of technical steps. The point is the *method*: how we research,
  document, drive the agent, and prove efficiency.
- Not a finished product. A small, well-explained case with a clear before/after beats an
  ambitious half-done one.

---

## 3. Base Repository (pick ONE, justify in README)

| Option | What it is | Best for |
|---|---|---|
| `soarsmu/BugsInPy` | Real bugs from real Python projects | Realistic investigation scenarios (⚠ needs solid venv/Docker skills) |
| `martinpeck/broken-python` | Collection of intentionally broken Python snippets | Debugging & code-improvement practice |
| `andela/buggy-python` | Scripts with bugs to test detection/fix ability | Bug identification & fixing |

**Requirement:** README must justify the choice and briefly explain *why this repo fits the assignment goals*.

> ⚠ If choosing `BugsInPy`: work in an isolated `virtualenv` or **Docker**. Don't start here unless
> the team is comfortable with Python environments and dependency hell.

---

## 4. Research Questions (must be answered explicitly in docs)

These must be addressed in the README, reports, and Obsidian pages:

1. What is the project's **actual** architecture, and what did we discover that wasn't obvious at first glance?
2. Which components / modules / classes / functions are the most **central**?
3. Where do **complexity hotspots**, mixed responsibilities, or **"God Nodes"** live?
4. How can architectural **block diagrams** and an **OOP schema** be extracted from the code, even when original docs are partial/missing?
5. How did we identify the bug, what was the **root cause**, and what steps led us to it?
6. What is the advantage of Obsidian's **graph navigation** vs. linear file reading?
7. How did the **graph-guided agent** save tokens / avoid redundant code reads?
8. What **extensions, improvements, or agent mechanisms** would we add next?

---

## 5. Core Tasks

### 5.1 — Build the Grphify representation + Obsidian docs
- Generate a graph representation of the codebase with **Grphify**.
- Build an **organized Obsidian vault** that acts as a *living knowledge space*, not just a file dump.
- Minimum pages:
  - **`index.md`** — central entry page: system structure + main navigation paths.
  - **`hot.md`** — focused context page for the bug-critical region.
  - Additional **Markdown** pages documenting key components, tests, findings, prime suspects, and the fix process.

### 5.2 — Reverse-engineer the unknown code
Extract from the code and present **at least two** central visualizations:
- **Architecture block diagram** — main parts of the system + data flow between them.
- **OOP schema** — classes, usage relations, composition, inheritance, wrappers, or relevant object patterns.

> A directory tree or file list is **not** enough — diagrams must reflect genuine engineering understanding.

### 5.3 — Debug via an AI agent
- Build an agent in **CrewAI** or **LangGraph** for investigation, localization, and explanation of the bug.
- The agent **must work graph-first**: rely initially on Grphify outputs + Obsidian pages, and only
  *then* request relevant code snippets.
- Document: how the **agent workflow** is structured, each agent/step's role, and the **context-reduction
  mechanism** built in to preserve efficiency.

### 5.4 — Fix and improve the code
- After localization, make a real fix in the code.
- Clearly present: what the problem was, why it happened, what changed, and how the fix was verified.
- Show a **before/after at the knowledge level too** — which Obsidian pages / nodes / links / insights
  changed once architecture understanding improved post-fix.

### 5.5 — Prove token savings
Run and compare **two modes**:
- **Naive mode** — agent/workflow operates over many raw files without sufficient focus.
- **Graph-guided mode** — agent operates via Grphify, `index.md`, `hot.md`, and Obsidian pages.

Comparison must include **at least**:
- Number of **tokens** consumed.
- Number of **files / textual units** read.
- Number of **iterations / investigation rounds**.
- **Quality / speed** of reaching root cause and fix.

### 5.6 — Extensions & original initiatives (required)
The base spec is a floor. In **every** part, propose at least one original extension / extra analysis /
improvement beyond minimum. Examples:
- Rank suspect nodes by **centrality** / **proximity** to failing tests.
- Generate **`hot.md` dynamically** from `graph.json` + `git diff`.
- Detect **orphan components** and auto-generate docs for them.
- Detect ambiguous links / mixed responsibilities and propose **refactoring**.
- Compare architecture before/after the fix via graphs/schemas.
- Generate an **impact report**: what breaks if a given class/function changes.

---

## 6. Planning & Efficiency Rules

Working with free/limited LLM accounts and rate limits — minimize scope, build context first, run the
agent only once context is organized.

### Do
- Pick **one** small/medium bug, not a whole system.
- Start with **Grphify** → produce `graph.json`, `hot.md`, `index.md` first.
- Use **Obsidian** to build a short work-map: the problem, suspects, what was checked, what was fixed.
- Activate the **AI** only after context is organized.
- Prefer **LangGraph** with a free/limited account (finer control over call count & steps).
- **Measure throughout**: files read, LLM calls, tokens saved.
- If using **BugsInPy**: isolated env, `virtualenv` or **Docker**.

### Don't
- Don't pick too many bugs or too large a project.
- Don't send the **entire codebase to the LLM at once**.
- Don't build a workflow with too many chatty agents / too many rounds.
- Don't start with BugsInPy without solid Python-env experience.
- Don't turn the assignment into a finished product — a small, well-explained case with clear before/after wins.
- Don't skip docs. Without a strong README, screenshots, diagrams, and an organized Obsidian vault, the process can't be proven.

---

## 7. Deliverables (GitHub repo)

- [ ] Complete **Python** solution code.
- [ ] **Agent workflow** implementation in CrewAI or LangGraph.
- [ ] Grphify outputs/artifacts — e.g. `graph.json`, `GRAPH_REPORT.md`, and parallel outputs.
- [ ] Full **Obsidian vault** with linked Markdown pages, including `index.md` and `hot.md`.
- [ ] **Bug analysis report**: problem description, root cause, investigation path, fix.
- [ ] **Token comparison report**: baseline vs. graph-guided.
- [ ] **Architecture block diagram.**
- [ ] **OOP schema.**
- [ ] **Before/after proof** for both the code fix and system understanding.
- [ ] Documentation of the team's **extensions and original ideas**.

---

## 8. README Requirements

`README.md` is a substantive part of the submission — rich, clear, readable by an external reader.
Must include:

- Description of the chosen repo + justification for the choice.
- Description of the bug / problem investigated.
- The research questions that guided the work.
- Overview of the architecture **as extracted from the code**.
- Description of the **agent workflow** built.
- Explanation of how **Grphify** and **Obsidian** were used.
- Explanation of the **reverse-engineering** process performed.
- Bug description, **root cause**, and the fix.
- Before/after comparison.
- **Token-efficiency** comparison.
- Detail of the team's extensions and original ideas.
- Clear **run instructions**.

**Plus visual elements:** screenshots, graphs, block diagrams, OOP schemas, flow diagrams, or any
other visualization that supports the analysis and presents the process.

---

## 9. Recommended Repository Structure

```
README.md
requirements.txt   (or pyproject.toml)
src/               # solution + agent workflow
tests/             # bug reproduction + fix verification
obsidian/          # vault: index.md, hot.md, linked notes
reports/           # bug analysis, token comparison, impact reports
artifacts/         # graph.json, GRAPH_REPORT.md, diagrams, screenshots
data/              # any input/fixtures
```

Adapt as needed, but keep it consistent, clear, and easy to navigate.

---

## 10. Expectations & Success Criteria

The expected work is **full engineering work** demonstrating understanding, initiative, and the
ability to produce a meaningful knowledge layer over existing code. We must show:

- Ability to debug **unfamiliar** code.
- Extraction of reverse-engineering insights.
- Schema production at the **architecture** and **OOP** levels (before/after).
- Real code improvement.
- **Obsidian-based proof** of the before → after state.

This is **not** a mechanical checklist. It evaluates *how* we research a system, *how* we document it,
*how* we operate an AI agent as an engineering tool, and *how* we prove that **graph-based,
focused context is more efficient than raw code reading**.

### Definition of Done
1. Graph + Obsidian vault built (`index.md`, `hot.md`, linked notes).
2. Architecture block diagram + OOP schema extracted and committed.
3. Graph-first AI agent (CrewAI/LangGraph) runs and locates the bug.
4. Bug fixed, verified, with documented root cause.
5. Token comparison report shows measurable savings (graph-guided < naive).
6. Before/after captured at both code and knowledge levels.
7. At least one original extension per part, documented.
8. README complete with all required sections + visuals.
