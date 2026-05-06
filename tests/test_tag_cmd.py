"""Unit tests for envdiff.tag_cmd."""
from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from envdiff.tag_cmd import run_tag_add, run_tag_list, run_tag_remove
from envdiff.tagger import save_tags


@pytest.fixture()
def tmp_env(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nSECRET=abc\n")
    return p


def _args(**kwargs) -> Namespace:
    defaults = {"format": "text", "dry_run": False, "label": None}
    defaults.update(kwargs)
    return Namespace(**defaults)


def test_tag_add_exits_zero(tmp_env: Path) -> None:
    args = _args(file=str(tmp_env), key="DB_HOST", label="infra")
    assert run_tag_add(args) == 0


def test_tag_add_missing_file_exits_one(tmp_path: Path) -> None:
    args = _args(file=str(tmp_path / "missing.env"), key="X", label="y")
    assert run_tag_add(args) == 1


def test_tag_add_json_output(tmp_env: Path, capsys) -> None:
    args = _args(file=str(tmp_env), key="DB_HOST", label="infra", format="json")
    run_tag_add(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "added" in data
    assert data["changed"] is True


def test_tag_remove_exits_zero(tmp_env: Path) -> None:
    save_tags(tmp_env, {"DB_HOST": ["infra"]})
    args = _args(file=str(tmp_env), key="DB_HOST", label="infra")
    assert run_tag_remove(args) == 0


def test_tag_remove_missing_file_exits_one(tmp_path: Path) -> None:
    args = _args(file=str(tmp_path / "missing.env"), key="X", label="y")
    assert run_tag_remove(args) == 1


def test_tag_list_exits_zero_empty(tmp_env: Path) -> None:
    args = _args(file=str(tmp_env))
    assert run_tag_list(args) == 0


def test_tag_list_missing_file_exits_one(tmp_path: Path) -> None:
    args = _args(file=str(tmp_path / "missing.env"))
    assert run_tag_list(args) == 1


def test_tag_list_json_output(tmp_env: Path, capsys) -> None:
    save_tags(tmp_env, {"DB_HOST": ["infra"], "SECRET": ["sensitive"]})
    args = _args(file=str(tmp_env), format="json")
    run_tag_list(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "DB_HOST" in data
    assert "infra" in data["DB_HOST"]


def test_tag_list_by_label(tmp_env: Path, capsys) -> None:
    save_tags(tmp_env, {"DB_HOST": ["infra"], "SECRET": ["sensitive"]})
    args = _args(file=str(tmp_env), label="infra", format="json")
    run_tag_list(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["keys"] == ["DB_HOST"]
