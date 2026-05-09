"""Tests for envdiff.tracer and envdiff.trace_cmd."""
from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from envdiff.tracer import trace_key, TraceReport
from envdiff.trace_cmd import run_trace, _render_text, _render_json


@pytest.fixture()
def tmp_env(tmp_path):
    def _write(name: str, content: str) -> str:
        p = tmp_path / name
        p.write_text(content)
        return str(p)
    return _write


def test_key_found_in_first_file(tmp_env):
    f1 = tmp_env("a.env", "DB_HOST=localhost\n")
    f2 = tmp_env("b.env", "DB_PORT=5432\n")
    report = trace_key("DB_HOST", [f1, f2])
    assert report.found
    assert report.effective_value == "localhost"


def test_origin_is_first_defining_file(tmp_env):
    f1 = tmp_env("base.env", "SECRET=base_val\n")
    f2 = tmp_env("prod.env", "SECRET=prod_val\n")
    report = trace_key("SECRET", [f1, f2])
    assert report.origin is not None
    assert report.origin.file == f1


def test_last_value_wins(tmp_env):
    f1 = tmp_env("base.env", "KEY=first\n")
    f2 = tmp_env("override.env", "KEY=second\n")
    report = trace_key("KEY", [f1, f2])
    assert report.effective_value == "second"


def test_absent_in_file_has_none_value(tmp_env):
    f1 = tmp_env("a.env", "OTHER=x\n")
    f2 = tmp_env("b.env", "KEY=hello\n")
    report = trace_key("KEY", [f1, f2])
    assert report.entries[0].value is None
    assert report.entries[1].value == "hello"


def test_key_not_found_anywhere(tmp_env):
    f1 = tmp_env("a.env", "UNRELATED=1\n")
    report = trace_key("MISSING", [f1])
    assert not report.found
    assert report.effective_value is None
    assert report.origin is None


def test_to_dict_structure(tmp_env):
    f1 = tmp_env("a.env", "FOO=bar\n")
    report = trace_key("FOO", [f1])
    d = report.to_dict()
    assert d["key"] == "FOO"
    assert d["found"] is True
    assert d["effective_value"] == "bar"
    assert isinstance(d["entries"], list)


def test_render_text_shows_origin_label(tmp_env):
    f1 = tmp_env("base.env", "API_KEY=abc\n")
    report = trace_key("API_KEY", [f1])
    text = _render_text(report)
    assert "ORIGIN" in text
    assert "abc" in text


def test_render_json_is_valid(tmp_env):
    f1 = tmp_env("a.env", "X=1\n")
    report = trace_key("X", [f1])
    parsed = json.loads(_render_json(report))
    assert parsed["key"] == "X"


def test_run_trace_exits_zero_when_found(tmp_env):
    f = tmp_env("a.env", "FOUND=yes\n")
    args = Namespace(key="FOUND", files=[f], format="text")
    assert run_trace(args) == 0


def test_run_trace_exits_one_when_missing(tmp_env):
    f = tmp_env("a.env", "OTHER=no\n")
    args = Namespace(key="MISSING", files=[f], format="text")
    assert run_trace(args) == 1


def test_run_trace_exits_one_for_bad_file(tmp_path):
    args = Namespace(key="X", files=[str(tmp_path / "ghost.env")], format="text")
    assert run_trace(args) == 1
