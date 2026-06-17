"""Tests for :mod:`arch_agent.shared.config`."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from arch_agent.shared.config import Config, load_config

REAL_CONFIG = Path(__file__).resolve().parents[1] / "config"


def _write(config_dir: Path, setup: dict[str, object], rate_limits: dict[str, object]) -> None:
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "setup.json").write_text(json.dumps(setup), encoding="utf-8")
    (config_dir / "rate_limits.json").write_text(json.dumps(rate_limits), encoding="utf-8")


def test_loads_real_project_config() -> None:
    config = load_config(REAL_CONFIG)
    assert config.target_repo == "https://github.com/andela/buggy-python"
    assert config.model == "claude-sonnet-4-6"
    assert "god_node_centrality" in config.graph_analysis
    assert "max_iterations" in config.agent_workflow


def test_accessors_and_defaults(tmp_path: Path) -> None:
    _write(
        tmp_path,
        {"version": "1.00", "target_repo": {"url": "u"}, "model": {"name": "m"}},
        {"version": "1.00"},
    )
    config = load_config(tmp_path)
    assert isinstance(config, Config)
    assert config.max_tokens == 4096  # default when absent
    assert config.graph_analysis == {}  # default when absent
    assert config.paths == {}


def test_explicit_max_tokens(tmp_path: Path) -> None:
    _write(
        tmp_path,
        {
            "version": "1.00",
            "target_repo": {"url": "u"},
            "model": {"name": "m", "max_tokens": 2000},
        },
        {"version": "1.00"},
    )
    assert load_config(tmp_path).max_tokens == 2000


def test_rejects_wrong_version(tmp_path: Path) -> None:
    _write(
        tmp_path,
        {"version": "0.9", "target_repo": {"url": "u"}, "model": {"name": "m"}},
        {"version": "1.00"},
    )
    with pytest.raises(ValueError, match="expected version"):
        load_config(tmp_path)


def test_rejects_non_object(tmp_path: Path) -> None:
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "setup.json").write_text("[1, 2, 3]", encoding="utf-8")
    (tmp_path / "rate_limits.json").write_text('{"version": "1.00"}', encoding="utf-8")
    with pytest.raises(ValueError, match="JSON object"):
        load_config(tmp_path)
