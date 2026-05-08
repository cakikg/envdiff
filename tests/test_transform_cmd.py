"""Tests for transform_cmd and renamer2."""
from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from envdiff.renamer2 import transform_env_file, transform_many
from envdiff.transform_cmd import run_transform


@pytest.fixture()
def tmp_env(tmp_path: Path):
    def _write(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")
        return p
    return _write


def _args(**kwargs) -> Namespace:
    defaults = {"files": [], "set": [], "dry_run": False, "format": "text"}
    defaults.update(kwargs)
    return Namespace(**defaults)


def test_transform_replaces_value(tmp_env):
    p = tmp_env("a.env", "DB_HOST=localhost\nDB_PORT=5432\n")
    result = transform_env_file(p, {"DB_HOST": "prod.db"})
    assert result.changed
    assert "DB_HOST" in result.replacements
    assert p.read_text().startswith("DB_HOST=prod.db")


def test_transform_dry_run_does_not_write(tmp_env):
    p = tmp_env("b.env", "SECRET=old\n")
    transform_env_file(p, {"SECRET": "new"}, dry_run=True)
    assert p.read_text() == "SECRET=old\n"


def test_transform_no_match_unchanged(tmp_env):
    p = tmp_env("c.env", "FOO=bar\n")
    result = transform_env_file(p, {"MISSING": "x"})
    assert not result.changed
    assert result.replacements == {}


def test_transform_many_multiple_files(tmp_env):
    p1 = tmp_env("d.env", "API_KEY=old1\n")
    p2 = tmp_env("e.env", "API_KEY=old2\n")
    results = transform_many([p1, p2], {"API_KEY": "newkey"})
    assert all(r.changed for r in results)
    assert p1.read_text() == "API_KEY=newkey\n"
    assert p2.read_text() == "API_KEY=newkey\n"


def test_cmd_exits_zero_on_change(tmp_env, capsys):
    p = tmp_env("f.env", "HOST=old\n")
    rc = run_transform(_args(files=[str(p)], set=["HOST=new"]))
    assert rc == 0
    out = capsys.readouterr().out
    assert "HOST" in out


def test_cmd_missing_file_exits_one(tmp_path, capsys):
    rc = run_transform(_args(files=[str(tmp_path / "ghost.env")], set=["K=v"]))
    assert rc == 1


def test_cmd_no_set_exits_one(tmp_env, capsys):
    p = tmp_env("g.env", "A=1\n")
    rc = run_transform(_args(files=[str(p)], set=[]))
    assert rc == 1


def test_cmd_json_output(tmp_env, capsys):
    p = tmp_env("h.env", "LEVEL=debug\n")
    rc = run_transform(_args(files=[str(p)], set=["LEVEL=info"], format="json"))
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data[0]["changed"] is True
    assert data[0]["replacements"]["LEVEL"] == "info"


def test_cmd_invalid_set_format_exits_one(tmp_env, capsys):
    p = tmp_env("i.env", "X=1\n")
    rc = run_transform(_args(files=[str(p)], set=["NOEQUALS"]))
    assert rc == 1
