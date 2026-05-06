"""Tests for envdiff.cascader."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from envdiff.cascader import cascade_env_files, override_summary


@pytest.fixture()
def tmp_env(tmp_path):
    def _write(name: str, content: str) -> str:
        p = tmp_path / name
        p.write_text(textwrap.dedent(content))
        return str(p)

    return _write


def test_base_only_no_overrides(tmp_env):
    f = tmp_env("base.env", "FOO=1\nBAR=2\n")
    result = cascade_env_files([f])
    assert result.resolved == {"FOO": "1", "BAR": "2"}
    assert not result.changed()


def test_later_file_wins(tmp_env):
    base = tmp_env("base.env", "FOO=base\n")
    prod = tmp_env("prod.env", "FOO=prod\n")
    result = cascade_env_files([base, prod])
    assert result.resolved["FOO"] == "prod"


def test_non_conflicting_keys_merged(tmp_env):
    a = tmp_env("a.env", "A=1\n")
    b = tmp_env("b.env", "B=2\n")
    result = cascade_env_files([a, b])
    assert result.resolved == {"A": "1", "B": "2"}
    assert not result.changed()


def test_override_recorded(tmp_env):
    base = tmp_env("base.env", "KEY=old\n")
    override = tmp_env("override.env", "KEY=new\n")
    result = cascade_env_files([base, override], show_values=True)
    assert "KEY" in result.overrides
    history = result.overrides["KEY"]
    assert history[0][0] == "old"
    assert history[1][0] == "new"


def test_provenance_tracks_source(tmp_env):
    base = tmp_env("base.env", "HOST=localhost\n")
    prod = tmp_env("prod.env", "HOST=prod.example.com\n")
    result = cascade_env_files([base, prod], show_values=True)
    val, src = result.provenance["HOST"]
    assert val == "prod.example.com"
    assert "prod.env" in src


def test_show_values_false_redacts(tmp_env):
    f = tmp_env("a.env", "SECRET=mysecret\n")
    result = cascade_env_files([f], show_values=False)
    val, _ = result.provenance["SECRET"]
    assert val == "***"
    # resolved dict still holds the real value
    assert result.resolved["SECRET"] == "mysecret"


def test_three_layers_last_wins(tmp_env):
    a = tmp_env("a.env", "X=1\n")
    b = tmp_env("b.env", "X=2\n")
    c = tmp_env("c.env", "X=3\n")
    result = cascade_env_files([a, b, c])
    assert result.resolved["X"] == "3"
    assert len(result.overrides["X"]) == 3


def test_override_summary_format(tmp_env):
    base = tmp_env("base.env", "DB=sqlite\n")
    prod = tmp_env("prod.env", "DB=postgres\n")
    result = cascade_env_files([base, prod], show_values=True)
    summary = override_summary(result)
    assert len(summary) == 1
    assert "DB" in summary[0]


def test_to_dict_structure(tmp_env):
    a = tmp_env("a.env", "K=v\n")
    result = cascade_env_files([a])
    d = result.to_dict()
    assert "resolved" in d
    assert "provenance" in d
    assert "overrides" in d


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        cascade_env_files([str(tmp_path / "nonexistent.env")])
