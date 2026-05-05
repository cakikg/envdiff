"""Tests for envdiff.duplicates_cmd."""
from pathlib import Path
import types

import pytest

from envdiff.duplicates_cmd import run_duplicates, _render_text, _render_json
from envdiff.duplicates import find_duplicates


@pytest.fixture()
def tmp_env(tmp_path):
    def _write(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")
        return p
    return _write


def _args(files, fmt="text"):
    ns = types.SimpleNamespace()
    ns.files = [str(f) for f in files]
    ns.format = fmt
    return ns


def test_clean_files_exit_zero(tmp_env):
    a = tmp_env("a.env", "FOO=1\n")
    b = tmp_env("b.env", "BAR=2\n")
    assert run_duplicates(_args([a, b])) == 0


def test_cross_file_duplicate_exits_one(tmp_env):
    a = tmp_env("a.env", "FOO=1\n")
    b = tmp_env("b.env", "FOO=2\n")
    assert run_duplicates(_args([a, b])) == 1


def test_within_file_duplicate_exits_one(tmp_env):
    a = tmp_env("a.env", "FOO=1\nFOO=2\n")
    assert run_duplicates(_args([a])) == 1


def test_missing_file_exits_one(tmp_env, capsys):
    result = run_duplicates(_args([Path("/no/such/file.env")]))
    assert result == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_render_text_clean(tmp_env):
    a = tmp_env("a.env", "FOO=1\n")
    report = find_duplicates([a])
    out = _render_text(report, [str(a)])
    assert "No duplicate" in out


def test_render_text_cross_file(tmp_env):
    a = tmp_env("a.env", "FOO=1\n")
    b = tmp_env("b.env", "FOO=2\n")
    report = find_duplicates([a, b])
    out = _render_text(report, [str(a), str(b)])
    assert "FOO" in out
    assert "Cross-file" in out


def test_render_json_format(tmp_env):
    import json
    a = tmp_env("a.env", "FOO=1\nFOO=2\n")
    report = find_duplicates([a])
    data = json.loads(_render_json(report))
    assert "within_file" in data
    assert "cross_file" in data


def test_json_flag_produces_json(tmp_env, capsys):
    import json
    a = tmp_env("a.env", "FOO=1\n")
    run_duplicates(_args([a], fmt="json"))
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, dict)
