# Improvements to Keep in Mind

> Distilled from the Assignment 1 feedback report and the lecturer's software
> guidelines, then tailored to **this** project (`graphify-obsidian-reverse-engineering`,
> EX04). Points specific to earlier assignments (signal/ML, debate UI) were dropped
> or rewritten for the graph-guided reverse-engineering context.

These are the things we lost points on before, plus what the EX04 brief emphasises.
Treat them as a standing checklist for the whole project.

## Planning & documentation
- [ ] Ship the **PRD up front** (see [`docs/PRD.md`](PRD.md), with the source brief in [`docs/assignment_brief.md`](assignment_brief.md)): problem, goals, design — written *before* the code so a new team member understands the vision without asking us.
- [ ] Keep docs current as the design evolves; document the *why* behind decisions, not just the *what*. The Obsidian vault must reflect the latest understanding (before → after).
- [ ] README must let any developer install and run the project with **zero prior knowledge** — clear run instructions are an explicit EX04 requirement.

## Configuration & security
- [ ] Config must be **portable**: it should set up cleanly in a completely different environment by someone who has never seen it. No hardcoded paths or environment assumptions.
- [ ] **No secrets in the repo.** LLM provider API keys come from environment / `.env`, never committed. Ship a `.env.example`.
- [ ] **Gatekeeper / trust boundary:** the agent feeds graph outputs, Obsidian notes, and raw code snippets back into the model — validate and sanitise anything crossing a trust boundary. Don't let untrusted file content drive privileged actions (e.g. tool calls, shell, file writes).

## Costs & resource awareness (CORE to EX04)
- [ ] This assignment is *graded on token efficiency.* Make the **cost model explicit**: tokens, files/textual units read, and iterations — for **both** the naive baseline and the graph-guided run.
- [ ] Instrument the agent to **measure throughout** (per call: tokens in/out, files touched, rounds). The token-comparison report is a required deliverable, so build the counters in from day one, not at the end.
- [ ] Respect free/limited-account rate limits: prefer **LangGraph** for finer control over call count and steps; activate the LLM only after context is organized.

## Extensibility
- [ ] Design for change: clean separation so a new base repo, a new agent step, a new graph metric, or a new output format can be added without breaking what works. Keep the LLM layer provider-agnostic (no ecosystem lock-in).

## Quality standards
- [ ] Establish **automated quality tooling** beyond manual review: linter + formatter (`ruff`), type checks, and tests wired into CI / pre-commit.
- [ ] **Testing**: reproduce the bug with a failing test *before* the fix, prove it green *after*. Cover edge cases (agent off-track, empty/failed graph query, malformed model output, missing nodes).

## Output clarity (docs / logs / visualization)
- [ ] Make behaviour legible at a glance: the **agent log** must show, per step, which agent ran, what context it pulled (graph node / Obsidian page / code snippet), and the tokens it spent.
- [ ] Required visuals must actually be present and readable: **architecture block diagram**, **OOP schema**, Obsidian graph screenshots, and before/after diagrams. Don't collapse everything into one overloaded view.

## Process
- [ ] Maintain disciplined **version control** with a visible development history, including the AI-assisted workflow. Commit `index.md`, `hot.md`, and `graph.json` as they evolve so the before → after is traceable in git.
