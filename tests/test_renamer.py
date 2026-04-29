"""Tests for envdiff.renamer and envdiff.rename_cmd."""
from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from envdiff.renamer import rename_key, rename_key_in_many, _rename_in_lines
from envdiff.rename_cmd import run_rename, _render_text, _render_json


@pytest.fixture()
def tmp_env(tmp_path: Path):
    def _write(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")
        return p

    return _write


# ── _rename_in_lines ──────────────────────────────────────────────────────────

def test_rename_replaces_key():
    lines = ["OLD_KEY=hello\n", "OTHER=world\n"]
    result, replaced = _rename_in_lines(lines, "OLD_KEY", "NEW_KEY")
    assert replaced
    assert result[0] == "NEW_KEY=hello\n"
    assert result[1] == "OTHER=world\n"


def test_rename_no_match_returns_false():
    lines = ["ALPHA=1\n"]
    _, replaced = _rename_in_lines(lines, "MISSING", "NEW")
    assert not replaced


def test_rename_preserves_spacing():
    lines = ["MY_KEY = value\n"]
    result, _ = _rename_in_lines(lines, "MY_KEY", "YOUR_KEY")
    assert result[0] == "YOUR_KEY = value\n"


def test_rename_does_not_touch_comments():
    lines = ["# OLD_KEY=ignored\n", "OLD_KEY=real\n"]
    result, replaced = _rename_in_lines(lines, "OLD_KEY", "NEW_KEY")
    assert replaced
    assert result[0] == "# OLD_KEY=ignored\n"  # comment untouched
    assert result[1] == "NEW_KEY=real\n"


# ── rename_key ────────────────────────────────────────────────────────────────

def test_rename_key_writes_file(tmp_env):
    p = tmp_env(".env", "FOO=bar\nBAZ=qux\n")
    result = rename_key(p, "FOO", "FOO_NEW")
    assert result.changed
    assert "FOO_NEW=bar" in p.read_text()


def test_rename_key_dry_run_does_not_write(tmp_env):
    p = tmp_env(".env", "FOO=bar\n")
    rename_key(p, "FOO", "FOO_NEW", dry_run=True)
    assert p.read_text() == "FOO=bar\n"


def test_rename_key_missing_key_not_changed(tmp_env):
    p = tmp_env(".env", "FOO=bar\n")
    result = rename_key(p, "NOPE", "NEW")
    assert not result.changed


# ── rename_key_in_many ────────────────────────────────────────────────────────

def test_rename_many_applies_to_all(tmp_env):
    p1 = tmp_env("a.env", "KEY=1\n")
    p2 = tmp_env("b.env", "KEY=2\n")
    results = rename_key_in_many([p1, p2], "KEY", "KEY2")
    assert all(r.changed for r in results)


# ── run_rename ────────────────────────────────────────────────────────────────

def test_run_rename_returns_zero_on_change(tmp_env):
    p = tmp_env(".env", "OLD=1\n")
    args = Namespace(files=[str(p)], old_key="OLD", new_key="NEW",
                     dry_run=False, format="text", verbose=False)
    assert run_rename(args) == 0


def test_run_rename_returns_two_when_key_not_found(tmp_env):
    p = tmp_env(".env", "ALPHA=1\n")
    args = Namespace(files=[str(p)], old_key="MISSING", new_key="X",
                     dry_run=False, format="text", verbose=False)
    assert run_rename(args) == 2


def test_run_rename_missing_file_returns_one(tmp_path):
    args = Namespace(files=[str(tmp_path / "ghost.env")], old_key="K",
                     new_key="K2", dry_run=False, format="text", verbose=False)
    assert run_rename(args) == 1


def test_run_rename_json_output(tmp_env, capsys):
    p = tmp_env(".env", "FOO=1\n")
    args = Namespace(files=[str(p)], old_key="FOO", new_key="BAR",
                     dry_run=True, format="json", verbose=False)
    run_rename(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data[0]["old_key"] == "FOO"
    assert data[0]["new_key"] == "BAR"
    assert data[0]["dry_run"] is True
