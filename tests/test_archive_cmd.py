"""Tests for envdiff.archive_cmd CLI handlers."""
from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from envdiff.archive_cmd import run_archive_create, run_archive_extract, run_archive_list


@pytest.fixture()
def tmp_env(tmp_path):
    def _write(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")
        return p

    return _write


def _args(**kwargs):
    ns = types.SimpleNamespace(format="text", no_redact=False)
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def test_create_exits_zero(tmp_env, tmp_path):
    f = tmp_env(".env", "KEY=val\n")
    dest = tmp_path / "out.zip"
    args = _args(files=[str(f)], output=str(dest))
    assert run_archive_create(args) == 0


def test_create_missing_file_exits_one(tmp_path):
    dest = tmp_path / "out.zip"
    args = _args(files=["/no/such/.env"], output=str(dest))
    assert run_archive_create(args) == 1


def test_create_json_output(tmp_env, tmp_path, capsys):
    f = tmp_env(".env", "A=1\n")
    dest = tmp_path / "out.zip"
    args = _args(files=[str(f)], output=str(dest), format="json")
    run_archive_create(args)
    out = json.loads(capsys.readouterr().out)
    assert "files_added" in out
    assert "size_bytes" in out


def test_list_exits_zero(tmp_env, tmp_path):
    f = tmp_env(".env", "X=1\n")
    dest = tmp_path / "out.zip"
    from envdiff.archiver import archive_env_files
    archive_env_files([f], dest)
    args = _args(archive=str(dest))
    assert run_archive_list(args) == 0


def test_list_missing_archive_exits_one(tmp_path):
    args = _args(archive=str(tmp_path / "nope.zip"))
    assert run_archive_list(args) == 1


def test_list_json_output(tmp_env, tmp_path, capsys):
    f = tmp_env(".env.dev", "Y=2\n")
    dest = tmp_path / "out.zip"
    from envdiff.archiver import archive_env_files
    archive_env_files([f], dest)
    args = _args(archive=str(dest), format="json")
    run_archive_list(args)
    names = json.loads(capsys.readouterr().out)
    assert ".env.dev" in names


def test_extract_exits_zero(tmp_env, tmp_path):
    f = tmp_env(".env", "K=v\n")
    dest = tmp_path / "out.zip"
    from envdiff.archiver import archive_env_files
    archive_env_files([f], dest)
    out_dir = tmp_path / "out"
    args = _args(archive=str(dest), dest=str(out_dir))
    assert run_archive_extract(args) == 0


def test_extract_missing_archive_exits_one(tmp_path):
    args = _args(archive=str(tmp_path / "ghost.zip"), dest=str(tmp_path / "out"))
    assert run_archive_extract(args) == 1
