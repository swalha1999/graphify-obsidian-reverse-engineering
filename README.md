# ArchAgent

Token-efficient architectural analysis & refactoring agent. ArchAgent turns an
unfamiliar Python repo into a knowledge graph with **Grphify**, browses it in
**Obsidian**, and runs a multi-agent crew to reverse-engineer the architecture,
detect structural smells, and prove token savings vs. feeding raw code to an LLM.

See [`docs/PRD.md`](docs/PRD.md), [`docs/PLAN.md`](docs/PLAN.md), and
[`docs/TODO.md`](docs/TODO.md) for the full specification and task board.

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
