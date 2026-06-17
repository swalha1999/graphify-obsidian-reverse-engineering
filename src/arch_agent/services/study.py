"""Token-efficiency study runs (PRD FR-13, PRD_token_efficiency.md §3-§4).

The same debugging ``task`` is run two ways and measured identically:

- :func:`run_baseline` (TODO 5.2) dumps **raw source** to the model — the naive
  control. It deliberately does not go through the graph-only agent guard.
- :func:`run_graph_guided` (TODO 5.3) feeds only the **graph artifacts**.

Both route calls through the gatekeeper and record tokens / files / units /
iterations / time via the :class:`EfficiencyMeter`. ``count_tokens`` is injectable
(default ~4 chars/token) so the comparison is consistent and tests are deterministic.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path

from arch_agent.agents.roles import ModelClient
from arch_agent.services.efficiency import EfficiencyMeter, RunRecord
from arch_agent.shared.gatekeeper import ApiGatekeeper

TokenCounter = Callable[[str], int]


def estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 characters per token)."""
    return max(1, len(text) // 4)


def _run_measured(
    *,
    task: str,
    context: str,
    files_read: int,
    units_read: int,
    client: ModelClient,
    gatekeeper: ApiGatekeeper,
    iterations: int,
    count_tokens: TokenCounter,
    clock: Callable[[], float],
    root_cause_found: bool,
    tests_green: bool,
) -> RunRecord:
    """Run ``iterations`` gatekept model calls over ``context`` and meter them."""
    meter = EfficiencyMeter(clock=clock)
    for _ in range(iterations):
        prompt = f"{task}\n\n{context}"
        completion = gatekeeper.execute(client, prompt)
        meter.record_call(
            count_tokens(prompt), count_tokens(completion), files=files_read, units=units_read
        )
        meter.record_iteration()
    meter.mark_root_cause()
    return meter.finish(root_cause_found=root_cause_found, tests_green=tests_green)


def run_baseline(
    repo_path: Path,
    task: str,
    client: ModelClient,
    gatekeeper: ApiGatekeeper,
    *,
    iterations: int = 1,
    count_tokens: TokenCounter = estimate_tokens,
    clock: Callable[[], float] = time.monotonic,
    root_cause_found: bool = True,
    tests_green: bool = True,
) -> RunRecord:
    """Naive control: dump every ``.py`` file to the model and measure the run."""
    files = sorted(repo_path.rglob("*.py"))
    raw = "\n\n".join(
        f"# file: {f.relative_to(repo_path)}\n{f.read_text(encoding='utf-8')}" for f in files
    )
    context = f"--- RAW SOURCE ({len(files)} files) ---\n{raw}"
    return _run_measured(
        task=task,
        context=context,
        files_read=len(files),
        units_read=raw.count("\n") + 1,
        client=client,
        gatekeeper=gatekeeper,
        iterations=iterations,
        count_tokens=count_tokens,
        clock=clock,
        root_cause_found=root_cause_found,
        tests_green=tests_green,
    )
