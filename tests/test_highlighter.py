"""Tests for envdiff.highlighter and envdiff.highlight_cmd."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from envdiff.highlighter import highlight_env_files
from envdiff.highlight_cmd import _render_text, _render_json, run_highlight


@pytest.fixture()
def tmp_env(tmp_path: Path):
    def _write(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(content)
        return p
    return _write


def test_identical_files_have_no_diff(tmp_env):
    a = tmp_env("a.env", "KEY=value\nFOO=bar\n")
    b = tmp_env("b.env", "KEY=value\nFOO=bar\n")
    report = highlight_env_files(a, b)
    assert not report.changed
    assert report.entries == []


def test_added_key_detected(tmp_env):
    a = tmp_env("a.env", "KEY=value\n")
    b = tmp_env("b.env", "KEY=value\nNEW=hello\n")
    report = highlight_env_files(a, b)
    assert report.changed
    assert len(report.added) == 1
    assert report.added[0].key == "NEW"
    assert report.added[0].new_value == "hello"
    assert report.added[0].old_value is None


def test_removed_key_detected(tmp_env):
    a = tmp_env("a.env", "KEY=value\nOLD=bye\n")
    b = tmp_env("b.env", "KEY=value\n")
    report = highlight_env_files(a, b)
    assert len(report.removed) == 1
    assert report.removed[0].key == "OLD"


def test_changed_key_detected(tmp_env):
    a = tmp_env("a.env", "KEY=old\n")
    b = tmp_env("b.env", "KEY=new\n")
    report = highlight_env_files(a, b)
    assert len(report.modified) == 1
    entry = report.modified[0]
    assert entry.key == "KEY"
    assert entry.old_value == "old"
    assert entry.new_value == "new"


def test_include_unchanged_flag(tmp_env):
    a = tmp_env("a.env", "KEY=same\n")
    b = tmp_env("b.env", "KEY=same\n")
    report = highlight_env_files(a, b, include_unchanged=True)
    assert len(report.entries) == 1
    assert report.entries[0].status == "unchanged"


def test_to_dict_structure(tmp_env):
    a = tmp_env("a.env", "A=1\n")
    b = tmp_env("b.env", "A=2\n")
    d = highlight_env_files(a, b).to_dict()
    assert "added" in d
    assert "removed" in d
    assert "modified" in d
    assert "entries" in d
    assert d["changed"] is True


def test_render_text_contains_key(tmp_env):
    a = tmp_env("a.env", "SECRET=old\n")
    b = tmp_env("b.env", "SECRET=new\n")
    report = highlight_env_files(a, b)
    text = _render_text(report, color=False)
    assert "SECRET" in text
    assert "old" in text
    assert "new" in text


def test_render_json_valid(tmp_env):
    a = tmp_env("a.env", "X=1\n")
    b = tmp_env("b.env", "X=2\n")
    report = highlight_env_files(a, b)
    data = json.loads(_render_json(report))
    assert data["changed"] is True


def test_run_highlight_exits_zero_for_identical(tmp_env):
    a = tmp_env("a.env", "K=v\n")
    b = tmp_env("b.env", "K=v\n")
    args = SimpleNamespace(file_a=str(a), file_b=str(b), format="text", color=False, unchanged=False)
    assert run_highlight(args) == 0


def test_run_highlight_exits_one_for_diff(tmp_env):
    a = tmp_env("a.env", "K=v1\n")
    b = tmp_env("b.env", "K=v2\n")
    args = SimpleNamespace(file_a=str(a), file_b=str(b), format="text", color=False, unchanged=False)
    assert run_highlight(args) == 1


def test_run_highlight_missing_file_exits_one(tmp_env, tmp_path):
    a = tmp_env("a.env", "K=v\n")
    args = SimpleNamespace(
        file_a=str(a),
        file_b=str(tmp_path / "missing.env"),
        format="text",
        color=False,
        unchanged=False,
    )
    assert run_highlight(args) == 1
