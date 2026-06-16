# ArchAgent

Token-efficient architectural analysis & refactoring agent. ArchAgent turns an
unfamiliar Python repo into a knowledge graph with **Grphify**, browses it in
**Obsidian**, and runs a multi-agent crew to reverse-engineer the architecture,
detect structural smells, and prove token savings vs. feeding raw code to an LLM.

See [`docs/PRD.md`](docs/PRD.md), [`docs/PLAN.md`](docs/PLAN.md), and
[`docs/TODO.md`](docs/TODO.md) for the full specification and task board.

## Target repository

We analyse **[`soarsmu/BugsInPy`](https://github.com/soarsmu/BugsInPy)** — a curated
benchmark of **real, reproducible bugs from real, mature Python projects**.

**Why we chose it:**

- **Realistic, not toy code.** BugsInPy draws bugs from established open-source projects, so
  the reverse-engineering is genuine — exactly the "debug unfamiliar real code" signal the
  assignment rewards, rather than small scripted snippets.
- **A built-in find → root-cause → fix → verify loop.** Each bug ships with a **buggy version,
  a fixed version, a failing test, and the test command**. That maps one-to-one onto our
  refactor loop (apply a change → re-run tests → keep only if green) and makes the
  **root-cause** and **before/after** write-ups precise and evidence-backed.
- **Richer knowledge graphs.** Real codebases yield far more modules/classes/edges than toy
  repos, so structural smells (**God Nodes**, high centrality, cycles) actually appear — and the
  **token-efficiency** win of reasoning over the graph instead of raw files is more pronounced.
- **Clean isolation.** BugsInPy pins each bug to a specific commit + environment, so the graph,
  metrics, and fix all refer to one well-defined system state.

**Trade-off & fallback.** BugsInPy is the most setup-intensive option (per-bug environments via
`virtualenv`/Docker). We scope to **one small/medium bug** and, if a specific bug proves too
hostile to set up, fall back to **[`andela/buggy-python`](https://github.com/andela/buggy-python)**
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
