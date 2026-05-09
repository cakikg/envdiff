"""Tests for envdiff.splitter."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from envdiff.splitter import split_env_file


@pytest.fixture()
def tmp_env(tmp_path):
    def _write(name: str, content: str) -> str:
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")
        return str(p)
    return _write


def test_split_creates_output_files(tmp_env, tmp_path):
    src = tmp_env("app.env", "DB_HOST=localhost\nDB_PORT=5432\nAPP_NAME=myapp\n")
    out_dir = str(tmp_path / "split")
    result = split_env_file(src, out_dir)
    assert result.changed
    for path in result.outputs.values():
        assert os.path.exists(path)


def test_split_dry_run_does_not_write(tmp_env, tmp_path):
    src = tmp_env("app.env", "DB_HOST=localhost\nAPP_NAME=myapp\n")
    out_dir = str(tmp_path / "split_dry")
    result = split_env_file(src, out_dir, dry_run=True)
    assert result.dry_run
    for path in result.outputs.values():
        assert not os.path.exists(path)


def test_split_keys_distributed_to_correct_group(tmp_env, tmp_path):
    src = tmp_env("app.env", "DB_HOST=localhost\nDB_PORT=5432\nAPP_DEBUG=true\n")
    out_dir = str(tmp_path / "split2")
    result = split_env_file(src, out_dir)
    assert "DB" in result.keys_written
    assert "DB_HOST" in result.keys_written["DB"]
    assert "DB_PORT" in result.keys_written["DB"]


def test_split_prefix_filter_limits_output(tmp_env, tmp_path):
    src = tmp_env("app.env", "DB_HOST=localhost\nAPP_NAME=myapp\n")
    out_dir = str(tmp_path / "split3")
    result = split_env_file(src, out_dir, prefix="DB")
    assert list(result.outputs.keys()) == ["DB"]


def test_split_empty_file_returns_unchanged(tmp_env, tmp_path):
    src = tmp_env("empty.env", "")
    out_dir = str(tmp_path / "split4")
    result = split_env_file(src, out_dir)
    assert not result.outputs


def test_split_to_dict_structure(tmp_env, tmp_path):
    src = tmp_env("app.env", "DB_HOST=localhost\n")
    out_dir = str(tmp_path / "split5")
    result = split_env_file(src, out_dir)
    d = result.to_dict()
    assert "source" in d
    assert "outputs" in d
    assert "keys_written" in d
    assert "dry_run" in d


def test_split_output_file_contains_key(tmp_env, tmp_path):
    src = tmp_env("app.env", "DB_HOST=localhost\nDB_PORT=5432\n")
    out_dir = str(tmp_path / "split6")
    result = split_env_file(src, out_dir)
    db_path = result.outputs.get("DB")
    assert db_path is not None
    content = Path(db_path).read_text(encoding="utf-8")
    assert "DB_HOST" in content
