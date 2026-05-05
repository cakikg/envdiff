"""Integration tests: profiler + profile_cmd work together end-to-end."""
from __future__ import annotations

import json
import textwrap
from argparse import Namespace
from pathlib import Path

import pytest

from envdiff.profile_cmd import run_profile
from envdiff.profiler import profile_env_file


ENV_CONTENT = """\
APP_NAME=myapp
PORT=8080
DEBUG=false
DATABASE_URL=postgres://user:secret@localhost/mydb
API_KEY=supersecret
EMPTY_VAR=
"""


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(textwrap.dedent(ENV_CONTENT))
    return p


def test_profile_counts_match_cmd_json(env_file, capsys):
    """profile_env_file and run_profile (json) agree on counts."""
    report = profile_env_file(env_file)
    rc = run_profile(Namespace(file=str(env_file), format="json", sensitive_pattern=[]))
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["total_keys"] == report.total_keys
    assert data["empty_keys"] == report.empty_keys
    assert data["sensitive_keys"] == report.sensitive_keys


def test_url_key_appears_in_url_keys(env_file):
    report = profile_env_file(env_file)
    assert "DATABASE_URL" in report.url_keys


def test_bool_key_classified_correctly(env_file):
    report = profile_env_file(env_file)
    assert "DEBUG" in report.bool_keys


def test_int_key_classified_correctly(env_file):
    report = profile_env_file(env_file)
    assert "PORT" in report.int_keys


def test_sensitive_key_detected(env_file):
    report = profile_env_file(env_file)
    assert "API_KEY" in report.sensitive_keys


def test_extra_sensitive_pattern_via_cmd(env_file, capsys):
    rc = run_profile(Namespace(
        file=str(env_file),
        format="json",
        sensitive_pattern=["APP_.*"],
    ))
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert "APP_NAME" in data["sensitive_keys"]
