# ArchAgent

Token-efficient architectural analysis & refactoring agent. ArchAgent turns an
unfamiliar Python repo into a knowledge graph with **Grphify**, browses it in
**Obsidian**, and runs a multi-agent crew to reverse-engineer the architecture,
detect structural smells, and prove token savings vs. feeding raw code to an LLM.

See [`docs/PRD.md`](docs/PRD.md), [`docs/PLAN.md`](docs/PLAN.md), and
[`docs/TODO.md`](docs/TODO.md) for the full specification and task board.

## Target repository

We analyse **[`andela/buggy-python`](https://github.com/andela/buggy-python)** — a small
collection of self-contained Python scripts that contain deliberate bugs, built specifically
to exercise bug **identification and fixing**.

**Why we chose it:**

- **Reproducible with zero setup friction.** It clones and runs with no per-bug `virtualenv`
  or Docker and no dependency hell, so our engineering effort goes into the *analysis, agent,
  and refactor* work — not environment wrangling. This directly follows the brief's warning not
  to let environment setup become a rabbit hole.
- **A clean find → root-cause → fix → verify loop.** The scripts are purpose-built for spotting
  and fixing bugs, which maps one-to-one onto our refactor loop (apply a change → re-run tests →
  keep only if green) and makes the **root-cause** and **before/after** write-ups precise.
- **A small, comprehensible graph — but still real architecture.** The codebase is large enough
  to surface genuine structural signal (centrality, fan-in/out, cycles, God-Node candidates) yet
  small enough that the graph and the diagrams stay readable and the findings are easy to verify.
- **Cheap and fast to iterate.** A compact graph keeps each `graphify extract` and every
  refactor-loop re-graph inexpensive, so the **token-efficiency study** stays well within budget
  and the loop can run more iterations under the same cap — and runs are deterministic and
  reliable on any grader's machine.

**Trade-off & fallback.** Being small, it tells a less dramatic "real bug in a mature library"
story than a benchmark like `soarsmu/BugsInPy`; for a scoped assignment we judged the clarity,
low cost, and reliability the better trade. If a richer target is wanted later,
**[`martinpeck/broken-python`](https://github.com/martinpeck/broken-python)** is the next step up
(documented in [`docs/GRAPHIFY_SETUP.md`](docs/GRAPHIFY_SETUP.md)).

> **Status:** scaffolding. This commit seeds the Python package and the CI
> quality gates; the service and agent layers land in later phases (see TODO).

## Requirements

- Python 3.12 (pinned in [`.python-version`](.python-version))
- [`uv`](https://docs.astral.sh/uv/) for dependency and task management

## Development

```bash
uv sync                                   # create the environment
uv run ruff check .                       # lint
uv run ruff format --check .              # format check
uv run mypy                               # type check
uv run pytest --cov --cov-report=term-missing   # tests + coverage (>=85%)
```

The same gates run in CI on every push and pull request
(see [`.github/workflows/ci.yml`](.github/workflows/ci.yml)).

## License

See repository for license terms.
