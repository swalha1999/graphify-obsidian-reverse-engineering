"""Tests for :mod:`arch_agent.services.gate`."""

from __future__ import annotations

from pathlib import Path

from arch_agent.services.gate import RefactorGate
from arch_agent.services.models import Edge, EdgeKind, GraphModel, Node, NodeType
from arch_agent.services.refactor import FileEdit, RefactorEngine
from arch_agent.services.verification import VerifyResult


class FakeReverifier:
    """Returns a canned VerifyResult; records that it was called."""

    def __init__(self, result: VerifyResult) -> None:
        self._result = result
        self.calls = 0

    def reverify(self, repo_path: Path, artifacts_dir: Path) -> VerifyResult:
        self.calls += 1
        return self._result


def _isolated_t() -> GraphModel:  # centrality(t) == 0.0
    return GraphModel("1.00", (Node("t", NodeType.MODULE), Node("a", NodeType.MODULE)), ())


def _central_t() -> GraphModel:  # centrality(t) == 1.0
    nodes = (Node("t", NodeType.MODULE), Node("a", NodeType.MODULE))
    return GraphModel("1.00", nodes, (Edge("a", "t", EdgeKind.IMPORT),))


def _gate(
    tmp_path: Path, result: VerifyResult, *, min_improvement: float = 0.0
) -> tuple[RefactorGate, Path]:
    target = tmp_path / "t.py"
    target.write_text("original", encoding="utf-8")
    engine = RefactorEngine(tmp_path)
    gate = RefactorGate(
        engine, FakeReverifier(result), tmp_path, tmp_path / "artifacts", min_improvement
    )
    return gate, target


def test_keeps_change_when_tests_pass_and_metric_improves(tmp_path: Path) -> None:
    gate, target = _gate(tmp_path, VerifyResult(tests_passed=True, graph=_isolated_t()))
    result = gate.attempt([FileEdit("t.py", "changed")], target_node="t", metric_before=0.5)
    assert result.kept is True
    assert result.reason == "improved"
    assert result.metric_after == 0.0
    assert target.read_text(encoding="utf-8") == "changed"  # NOT reverted


def test_reverts_when_tests_fail(tmp_path: Path) -> None:
    gate, target = _gate(tmp_path, VerifyResult(tests_passed=False, graph=_isolated_t()))
    result = gate.attempt([FileEdit("t.py", "changed")], target_node="t", metric_before=0.5)
    assert result.kept is False
    assert result.reason == "tests_failed"
    assert target.read_text(encoding="utf-8") == "original"  # reverted (ADR-004)


def test_reverts_when_metric_does_not_improve(tmp_path: Path) -> None:
    gate, target = _gate(tmp_path, VerifyResult(tests_passed=True, graph=_central_t()))
    result = gate.attempt([FileEdit("t.py", "changed")], target_node="t", metric_before=0.5)
    assert result.kept is False
    assert result.reason == "no_improvement"  # centrality went up (1.0 > 0.5)
    assert target.read_text(encoding="utf-8") == "original"


def test_reverts_when_improvement_below_threshold(tmp_path: Path) -> None:
    gate, target = _gate(
        tmp_path, VerifyResult(tests_passed=True, graph=_isolated_t()), min_improvement=0.05
    )
    # delta = 0.04 - 0.0 = 0.04 < 0.05 -> not enough
    result = gate.attempt([FileEdit("t.py", "changed")], target_node="t", metric_before=0.04)
    assert result.kept is False
    assert result.reason == "no_improvement"
    assert target.read_text(encoding="utf-8") == "original"
