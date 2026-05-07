"""Tests for envdiff.referencer and envdiff.reference_cmd."""
from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from envdiff.referencer import find_key_references, ReferenceReport
from envdiff.reference_cmd import run_reference, _render_text, _render_json


@pytest.fixture()
def tmp_env(tmp_path):
    def _write(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(content)
        return p
    return _write


# ---------------------------------------------------------------------------
# referencer unit tests
# ---------------------------------------------------------------------------

def test_key_found_in_all_files(tmp_env):
    a = tmp_env("a.env", "FOO=1\nBAR=2\n")
    b = tmp_env("b.env", "FOO=3\nBAZ=4\n")
    report = find_key_references("FOO", [a, b])
    assert report.clean
    assert str(a) in report.found_in
    assert str(b) in report.found_in
    assert report.missing_in == []


def test_key_missing_from_one_file(tmp_env):
    a = tmp_env("a.env", "FOO=1\n")
    b = tmp_env("b.env", "BAR=2\n")
    report = find_key_references("FOO", [a, b])
    assert not report.clean
    assert str(a) in report.found_in
    assert str(b) in report.missing_in


def test_key_missing_from_all_files(tmp_env):
    a = tmp_env("a.env", "BAR=1\n")
    b = tmp_env("b.env", "BAZ=2\n")
    report = find_key_references("GHOST", [a, b])
    assert not report.clean
    assert report.found_in == []
    assert len(report.missing_in) == 2


def test_file_not_found_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        find_key_references("FOO", [tmp_path / "nope.env"])


def test_to_dict_structure(tmp_env):
    a = tmp_env("a.env", "FOO=1\n")
    report = find_key_references("FOO", [a])
    d = report.to_dict()
    assert set(d.keys()) == {"key", "found_in", "missing_in", "clean"}
    assert d["key"] == "FOO"
    assert d["clean"] is True


# ---------------------------------------------------------------------------
# reference_cmd tests
# ---------------------------------------------------------------------------

def _args(key, files, fmt="text"):
    return Namespace(key=key, files=[str(f) for f in files], format=fmt)


def test_run_reference_exits_zero_when_clean(tmp_env):
    a = tmp_env("a.env", "FOO=1\n")
    assert run_reference(_args("FOO", [a])) == 0


def test_run_reference_exits_one_when_missing(tmp_env):
    a = tmp_env("a.env", "BAR=2\n")
    assert run_reference(_args("FOO", [a])) == 1


def test_run_reference_missing_file_exits_one(tmp_path):
    rc = run_reference(_args("FOO", [tmp_path / "missing.env"]))
    assert rc == 1


def test_render_json_is_valid(tmp_env):
    a = tmp_env("a.env", "FOO=1\n")
    report = find_key_references("FOO", [a])
    data = json.loads(_render_json(report))
    assert data["key"] == "FOO"
    assert data["clean"] is True


def test_render_text_shows_found(tmp_env):
    a = tmp_env("a.env", "FOO=1\n")
    report = find_key_references("FOO", [a])
    text = _render_text(report)
    assert "Found in" in text
    assert str(a) in text


def test_render_text_shows_missing(tmp_env):
    a = tmp_env("a.env", "BAR=2\n")
    report = find_key_references("FOO", [a])
    text = _render_text(report)
    assert "Missing in" in text
    assert "MISSING" in text
