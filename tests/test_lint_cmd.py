"""Tests for envdiff.lint_cmd."""
import json
import textwrap
from types import SimpleNamespace

import pytest

from envdiff.lint_cmd import run_lint


@pytest.fixture()
def tmp_env(tmp_path):
    def _write(name: str, content: str) -> str:
        p = tmp_path / name
        p.write_text(textwrap.dedent(content))
        return str(p)
    return _write


def _args(files, fmt="text", color=False):
    return SimpleNamespace(files=files, format=fmt, color=color)


def test_clean_file_exits_zero(tmp_env):
    path = tmp_env(".env", "FOO=bar\nBAZ=qux\n")
    code = run_lint(_args([path]))
    assert code == 0


def test_duplicate_key_exits_nonzero(tmp_env):
    path = tmp_env(".env", "KEY=a\nKEY=b\n")
    code = run_lint(_args([path]))
    assert code != 0


def test_missing_file_exits_nonzero(capsys):
    code = run_lint(_args(["/no/such/.env"]))
    assert code != 0


def test_json_output_structure(tmp_env, capsys):
    path = tmp_env(".env", "KEY=a\nKEY=b\n")
    run_lint(_args([path], fmt="json"))
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert "file" in data[0]
    assert "issues" in data[0]
    assert "ok" in data[0]


def test_json_clean_file_ok_true(tmp_env, capsys):
    path = tmp_env(".env", "FOO=bar\n")
    run_lint(_args([path], fmt="json"))
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data[0]["ok"] is True
    assert data[0]["issues"] == []


def test_multiple_files_all_checked(tmp_env):
    p1 = tmp_env("a.env", "KEY=a\nKEY=b\n")
    p2 = tmp_env("b.env", "FOO=ok\n")
    code = run_lint(_args([p1, p2]))
    assert code != 0  # p1 has error
