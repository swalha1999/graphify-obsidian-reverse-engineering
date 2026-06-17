# Prompt Book

A log of the **significant prompts** ArchAgent sends, with their context and the real
outputs they produced on the `andela/buggy-python` run (TODO 6.6).

The system never free-types prompts ad hoc — every agent prompt is assembled by one base
template and is **guarded to contain graph artifacts only, never raw source** (FR 3.5,
`agents/guards.py`). That guard is itself the most important "prompt rule": it raises
before any model call if the context looks like a code dump.

---

## 1. The prompt template (`agents/roles.py`)

Every agent builds its prompt the same way:

```
You are the {name} agent. {responsibility}

---
{context}
```

- `{responsibility}` is the agent's single responsibility (its system instruction, below).
- `{context}` is **curated graph artifacts** — `index.md` + `hot.md` for the Explorer,
  the rendered findings for the Analyst, the prior agent's output downstream — never `.py`.

## 2. The five role instructions

| Agent | `{responsibility}` (the steering instruction) |
|---|---|
| **Explorer** | *Summarise the system architecture using only the curated index.md and hot.md notes — never raw source files.* |
| **Analyst** | *Identify structural risk: rank the architectural smells with evidence drawn from the graph metrics.* |
| **Architect** | *Decide what to change: produce ordered, justified refactoring recommendations.* |
| **Refactor** | *Execute one change safely: produce a minimal patch for the top recommendation, touching only what is needed.* |
| **Reporter** | *Communicate results: write the before/after architecture and token report.* |

The crew runs them as a LangGraph state machine: **explore → analyse → recommend → report**.

---

## 3. Worked example — the Architect (the sharpest output of the run)

**Context fed in** (graph-derived findings rendered by the crew, not source):

```
Detected smells:
- [low] god_node @ snippets_io: High centrality / fan-in: a structural single point of failure.
- [low] god_node @ snippets_foobar_foo: High centrality / fan-in: a structural single point of failure.
- [low] spof @ snippets_foobar_foo: Articulation point with high fan-in: its removal disconnects the graph.
```

**Output produced** (excerpt from [`reports/recommendations.md`](../reports/recommendations.md)) —
note it *critiqued the evidence* before recommending:

> Before issuing recommendations I need to flag one analytical issue … **Rank 3 is listed
> as a separate entry for `snippets_foobar_foo` but correctly identified as subsumed by
> Rank 1**. I will treat that node as a single subject. …
>
> ### Recommendation 1 — Decompose `snippets_foobar_foo` to Eliminate the Articulation Point
> … the articulation-point property is the harder constraint: it is a *topological*
> property of the dependency graph, not just a code quality concern.

That reasoning — recognising an articulation point as a topological, not cosmetic, problem
— is exactly the architecture-level judgement the prompt was designed to elicit.

---

## 4. The token-study prompts (baseline vs graph-guided)

The same task is sent two ways (`services/study.py`); the *only* difference is the context:

- **Baseline (naive control):** `"{task}\n\n--- RAW SOURCE (N files) ---\n{every .py file dumped}"`.
- **Graph-guided:** `"{task}\n\n--- GRAPH ARTIFACTS (N files) ---\n{index.md + hot.md}"`.

Measured result: the graph-guided prompt carried **~2.4× fewer input tokens** and the run
used **50.3% fewer total tokens** ([`reports/token_efficiency.md`](../reports/token_efficiency.md)).

---

## 5. Why so few "prompts"

ArchAgent deliberately minimises bespoke prompting: thresholds and stop criteria are
**config**, not prose; agents read **graph artifacts**, not files; and the guard enforces
that. The result is a small, auditable prompt surface — which is the whole token-efficiency
argument restated at the prompt level.
