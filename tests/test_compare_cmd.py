"""Tests for envdiff.compare_cmd."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from envdiff.compare_cmd import run_compare, _render_text, _render_json
from envdiff.comparator import compare_envs


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


def _args(**kwargs):
    defaults = {"format": "text", "names": None, "show_values": False}
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# run_compare exit codes
# ---------------------------------------------------------------------------

def test_identical_files_exits_zero(tmp_path):
    a = _write(tmp_path, "a.env", "FOO=1\n")
    b = _write(tmp_path, "b.env", "FOO=1\n")
    assert run_compare(_args(files=[str(a), str(b)])) == 0


def test_missing_key_exits_one(tmp_path):
    a = _write(tmp_path, "a.env", "FOO=1\nBAR=2\n")
    b = _write(tmp_path, "b.env", "FOO=1\n")
    assert run_compare(_args(files=[str(a), str(b)])) == 1


def test_missing_file_exits_one(tmp_path):
    a = _write(tmp_path, "a.env", "FOO=1\n")
    code = run_compare(_args(files=[str(a), str(tmp_path / "ghost.env")]))
    assert code == 1


def test_name_length_mismatch_exits_one(tmp_path):
    a = _write(tmp_path, "a.env", "FOO=1\n")
    b = _write(tmp_path, "b.env", "FOO=1\n")
    code = run_compare(_args(files=[str(a), str(b)], names="only_one"))
    assert code == 1


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------

def test_json_output_is_valid(tmp_path, capsys):
    a = _write(tmp_path, "a.env", "FOO=1\n")
    b = _write(tmp_path, "b.env", "FOO=1\n")
    run_compare(_args(files=[str(a), str(b)], format="json"))
    captured = capsys.readouterr().out
    data = json.loads(captured)
    assert "all_ok" in data
    assert "keys" in data


def test_json_flags_missing_key(tmp_path, capsys):
    a = _write(tmp_path, "a.env", "FOO=1\nBAR=2\n")
    b = _write(tmp_path, "b.env", "FOO=1\n")
    run_compare(_args(files=[str(a), str(b)], format="json"))
    data = json.loads(capsys.readouterr().out)
    bar = next(k for k in data["keys"] if k["key"] == "BAR")
    assert bar["missing_in"] != []


# ---------------------------------------------------------------------------
# text rendering helpers
# ---------------------------------------------------------------------------

def test_render_text_contains_ok_label(tmp_path):
    a = _write(tmp_path, "a.env", "FOO=1\n")
    b = _write(tmp_path, "b.env", "FOO=1\n")
    report = compare_envs([a, b])
    text = _render_text(report)
    assert "OK" in text


def test_render_text_contains_missing_label(tmp_path):
    a = _write(tmp_path, "a.env", "FOO=1\nBAR=2\n")
    b = _write(tmp_path, "b.env", "FOO=1\n")
    report = compare_envs([a, b])
    text = _render_text(report)
    assert "MISSING" in text
