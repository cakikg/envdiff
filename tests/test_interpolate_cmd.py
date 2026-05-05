"""Tests for envdiff.interpolate_cmd."""
import json
from argparse import Namespace
from pathlib import Path

import pytest

from envdiff.interpolate_cmd import run_interpolate


@pytest.fixture()
def tmp_env(tmp_path):
    return tmp_path / ".env"


def _write(p: Path, content: str) -> Path:
    p.write_text(content)
    return p


def _args(file, format="text", show_values=False, use_os_env=False):
    return Namespace(
        file=str(file),
        format=format,
        show_values=show_values,
        use_os_env=use_os_env,
    )


def test_clean_file_exits_zero(tmp_env):
    _write(tmp_env, "FOO=bar\nBAZ=qux\n")
    assert run_interpolate(_args(tmp_env)) == 0


def test_missing_ref_exits_one(tmp_env):
    _write(tmp_env, "FOO=${UNDEFINED}\n")
    assert run_interpolate(_args(tmp_env)) == 1


def test_missing_file_exits_one(tmp_path):
    assert run_interpolate(_args(tmp_path / "no_such.env")) == 1


def test_json_format_output(tmp_env, capsys):
    _write(tmp_env, "BASE=/app\nDATA=${BASE}/data\n")
    rc = run_interpolate(_args(tmp_env, format="json", show_values=True))
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["resolved"]["DATA"] == "/app/data"
    assert data["ok"] is True


def test_json_hides_values_by_default(tmp_env, capsys):
    _write(tmp_env, "SECRET=hunter2\n")
    run_interpolate(_args(tmp_env, format="json", show_values=False))
    data = json.loads(capsys.readouterr().out)
    assert data["resolved"]["SECRET"] == "***"


def test_text_format_shows_resolved_keys(tmp_env, capsys):
    _write(tmp_env, "A=hello\nB=${A}\n")
    run_interpolate(_args(tmp_env, format="text", show_values=True))
    out = capsys.readouterr().out
    assert "B=hello" in out
