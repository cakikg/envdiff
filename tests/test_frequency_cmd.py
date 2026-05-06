"""Tests for envdiff.frequency_cmd."""
from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from envdiff.frequency_cmd import run_frequency


@pytest.fixture()
def tmp_env(tmp_path):
    def _write(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(content)
        return p
    return _write


def _args(files, fmt="text", threshold=1.0, show_rare=False):
    return Namespace(files=[str(f) for f in files], format=fmt,
                     threshold=threshold, show_rare=show_rare)


def test_missing_file_exits_one(tmp_path):
    args = _args([tmp_path / "ghost.env"])
    assert run_frequency(args) == 1


def test_clean_files_exit_zero(tmp_env):
    p1 = tmp_env("a.env", "FOO=1\n")
    p2 = tmp_env("b.env", "FOO=2\n")
    assert run_frequency(_args([p1, p2])) == 0


def test_json_output_is_valid(tmp_env, capsys):
    p = tmp_env("a.env", "FOO=1\nBAR=2\n")
    run_frequency(_args([p], fmt="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "counts" in data
    assert "coverage" in data


def test_text_output_contains_key(tmp_env, capsys):
    p = tmp_env("a.env", "MY_KEY=hello\n")
    run_frequency(_args([p]))
    out = capsys.readouterr().out
    assert "MY_KEY" in out


def test_rare_flag_shows_rare_section(tmp_env, capsys):
    p1 = tmp_env("a.env", "FOO=1\nRAREKEY=x\n")
    p2 = tmp_env("b.env", "FOO=2\n")
    run_frequency(_args([p1, p2], show_rare=True, threshold=1.0))
    out = capsys.readouterr().out
    assert "Rare keys" in out
    assert "RAREKEY" in out
