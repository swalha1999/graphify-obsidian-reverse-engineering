"""Tests for :mod:`arch_agent.services.refactor`."""

from __future__ import annotations

from pathlib import Path

from arch_agent.services.refactor import FileEdit, RefactorEngine


def test_apply_modifies_existing_and_revert_restores(tmp_path: Path) -> None:
    f = tmp_path / "mod.py"
    f.write_text("original", encoding="utf-8")
    engine = RefactorEngine(tmp_path)

    engine.apply([FileEdit("mod.py", "changed")])
    assert f.read_text(encoding="utf-8") == "changed"
    assert engine.applied

    engine.revert()
    assert f.read_text(encoding="utf-8") == "original"
    assert not engine.applied


def test_apply_creates_new_file_and_revert_deletes(tmp_path: Path) -> None:
    engine = RefactorEngine(tmp_path)
    engine.apply([FileEdit("pkg/new_mod.py", "x = 1")])
    new_file = tmp_path / "pkg" / "new_mod.py"
    assert new_file.read_text(encoding="utf-8") == "x = 1"

    engine.revert()
    assert not new_file.exists()


def test_split_module_refactor(tmp_path: Path) -> None:
    original = tmp_path / "payments.py"
    original.write_text("# big god module\n", encoding="utf-8")
    engine = RefactorEngine(tmp_path)

    engine.apply(
        [
            FileEdit("payments.py", "from payments_io import save\n"),
            FileEdit("payments_io.py", "def save(): ...\n"),
        ]
    )
    assert "payments_io" in original.read_text(encoding="utf-8")
    assert (tmp_path / "payments_io.py").is_file()

    engine.revert()
    assert original.read_text(encoding="utf-8") == "# big god module\n"
    assert not (tmp_path / "payments_io.py").exists()


def test_snapshot_taken_once_so_revert_restores_original(tmp_path: Path) -> None:
    f = tmp_path / "mod.py"
    f.write_text("v0", encoding="utf-8")
    engine = RefactorEngine(tmp_path)
    engine.apply([FileEdit("mod.py", "v1")])
    engine.apply([FileEdit("mod.py", "v2")])  # second touch must not re-snapshot
    assert f.read_text(encoding="utf-8") == "v2"
    engine.revert()
    assert f.read_text(encoding="utf-8") == "v0"  # back to the true original


def test_revert_with_no_edits_is_noop(tmp_path: Path) -> None:
    RefactorEngine(tmp_path).revert()  # must not raise
