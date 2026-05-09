"""Tests for envdiff.split_cmd."""
from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from envdiff.split_cmd import run_split


@pytest.fixture()
def tmp_env(tmp_path):
    def _write(name: str, content: str) -> str:
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")
        return str(p)
    return _write


def _args(tmp_path, file: str, **kwargs) -> Namespace:
    out_dir = str(tmp_path / "out")
    return Namespace(file=file, output_dir=out_dir, prefix=None, dry_run=False, format="text", **kwargs)


def test_split_exits_zero(tmp_env, tmp_path):
    src = tmp_env("app.env", "DB_HOST=localhost\nAPP_NAME=myapp\n")
    rc = run_split(_args(tmp_path, src))
    assert rc == 0


def test_split_missing_file_exits_one(tmp_path):
    args = Namespace(file="/no/such/file.env", output_dir=str(tmp_path / "out"),
                     prefix=None, dry_run=False, format="text")
    rc = run_split(args)
    assert rc == 1


def test_split_json_format_is_valid(tmp_env, tmp_path, capsys):
    src = tmp_env("app.env", "DB_HOST=localhost\n")
    args = _args(tmp_path, src, format="json")
    run_split(args)
    captured = capsys.readouterr().out
    data = json.loads(captured)
    assert "outputs" in data
    assert "keys_written" in data


def test_split_dry_run_text_mentions_dry_run(tmp_env, tmp_path, capsys):
    src = tmp_env("app.env", "DB_HOST=localhost\n")
    args = Namespace(file=src, output_dir=str(tmp_path / "out"),
                     prefix=None, dry_run=True, format="text")
    run_split(args)
    captured = capsys.readouterr().out
    assert "dry-run" in captured


def test_split_prefix_filter_in_json(tmp_env, tmp_path, capsys):
    src = tmp_env("app.env", "DB_HOST=localhost\nAPP_NAME=myapp\n")
    args = Namespace(file=src, output_dir=str(tmp_path / "out"),
                     prefix="DB", dry_run=False, format="json")
    run_split(args)
    data = json.loads(capsys.readouterr().out)
    assert list(data["outputs"].keys()) == ["DB"]
