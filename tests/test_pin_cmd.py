"""Tests for envdiff.pin_cmd."""
import argparse
import json
from pathlib import Path

import pytest

from envdiff.pin_cmd import run_drift, run_pin
from envdiff.pinner import pin_env


@pytest.fixture
def tmp_env(tmp_path):
    return tmp_path / ".env"


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def _args(**kwargs):
    defaults = {"file": None, "lock": None, "format": "text"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_pin_exits_zero(tmp_env):
    _write(tmp_env, "KEY=value\nOTHER=123\n")
    code = run_pin(_args(file=str(tmp_env)))
    assert code == 0


def test_pin_missing_file_exits_one(tmp_env):
    code = run_pin(_args(file=str(tmp_env)))
    assert code == 1


def test_pin_creates_lock_file(tmp_env):
    _write(tmp_env, "KEY=value\n")
    lock = tmp_env.parent / ".env.lock"
    run_pin(_args(file=str(tmp_env)))
    assert lock.exists()


def test_drift_exits_zero_when_clean(tmp_env):
    _write(tmp_env, "KEY=value\n")
    run_pin(_args(file=str(tmp_env)))
    code = run_drift(_args(file=str(tmp_env)))
    assert code == 0


def test_drift_exits_one_when_changed(tmp_env):
    _write(tmp_env, "KEY=value\n")
    run_pin(_args(file=str(tmp_env)))
    _write(tmp_env, "KEY=changed\n")
    code = run_drift(_args(file=str(tmp_env)))
    assert code == 1


def test_drift_missing_env_exits_one(tmp_env):
    code = run_drift(_args(file=str(tmp_env)))
    assert code == 1


def test_drift_missing_lock_exits_one(tmp_env):
    _write(tmp_env, "KEY=value\n")
    code = run_drift(_args(file=str(tmp_env)))
    assert code == 1


def test_drift_json_format_is_valid(tmp_env, capsys):
    _write(tmp_env, "KEY=value\n")
    run_pin(_args(file=str(tmp_env)))
    _write(tmp_env, "KEY=new\nEXTRA=1\n")
    run_drift(_args(file=str(tmp_env), format="json"))
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "changed" in data
    assert "added" in data
    assert "clean" in data
