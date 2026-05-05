"""Tests for envdiff.profile_cmd."""
from __future__ import annotations

import json
import textwrap
from argparse import Namespace
from pathlib import Path

import pytest

from envdiff.profile_cmd import run_profile


@pytest.fixture()
def tmp_env(tmp_path: Path):
    def _write(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(textwrap.dedent(content))
        return p
    return _write


def _args(file: str, fmt: str = "text", sensitive_pattern=None) -> Namespace:
    return Namespace(file=file, format=fmt, sensitive_pattern=sensitive_pattern or [])


def test_missing_file_exits_one(tmp_path):
    rc = run_profile(_args(str(tmp_path / "missing.env")))
    assert rc == 1


def test_clean_file_exits_zero(tmp_env):
    p = tmp_env("HOST=localhost\nPORT=5432\n")
    rc = run_profile(_args(str(p)))
    assert rc == 0


def test_text_output_contains_total(tmp_env, capsys):
    p = tmp_env("HOST=localhost\nPORT=5432\n")
    run_profile(_args(str(p)))
    out = capsys.readouterr().out
    assert "Total keys" in out
    assert "2" in out


def test_json_output_is_valid_json(tmp_env, capsys):
    p = tmp_env("HOST=localhost\n")
    run_profile(_args(str(p), fmt="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["total_keys"] == 1


def test_json_output_includes_path(tmp_env, capsys):
    p = tmp_env("HOST=localhost\n")
    run_profile(_args(str(p), fmt="json"))
    data = json.loads(capsys.readouterr().out)
    assert str(p) in data["path"]


def test_empty_keys_shown_in_text(tmp_env, capsys):
    p = tmp_env("SECRET=\n")
    run_profile(_args(str(p)))
    out = capsys.readouterr().out
    assert "SECRET" in out
