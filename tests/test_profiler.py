"""Tests for envdiff.profiler."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from envdiff.profiler import profile_env_file


@pytest.fixture()
def tmp_env(tmp_path: Path):
    def _write(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(textwrap.dedent(content))
        return p
    return _write


def test_total_keys(tmp_env):
    p = tmp_env("""\
        HOST=localhost
        PORT=5432
        DEBUG=true
    """)
    r = profile_env_file(p)
    assert r.total_keys == 3


def test_empty_keys_detected(tmp_env):
    p = tmp_env("""\
        HOST=localhost
        SECRET=
    """)
    r = profile_env_file(p)
    assert "SECRET" in r.empty_keys
    assert "HOST" not in r.empty_keys


def test_sensitive_keys_detected(tmp_env):
    p = tmp_env("""\
        DATABASE_PASSWORD=hunter2
        HOST=localhost
    """)
    r = profile_env_file(p)
    assert "DATABASE_PASSWORD" in r.sensitive_keys
    assert "HOST" not in r.sensitive_keys


def test_url_keys_detected(tmp_env):
    p = tmp_env("""\
        DATABASE_URL=postgres://user:pass@localhost/db
        HOST=localhost
    """)
    r = profile_env_file(p)
    assert "DATABASE_URL" in r.url_keys
    assert "HOST" not in r.url_keys


def test_int_keys_detected(tmp_env):
    p = tmp_env("""\
        PORT=5432
        HOST=localhost
    """)
    r = profile_env_file(p)
    assert "PORT" in r.int_keys


def test_bool_keys_detected(tmp_env):
    p = tmp_env("""\
        DEBUG=true
        ENABLED=false
        HOST=localhost
    """)
    r = profile_env_file(p)
    assert "DEBUG" in r.bool_keys
    assert "ENABLED" in r.bool_keys


def test_string_keys_detected(tmp_env):
    p = tmp_env("""\
        APP_NAME=myapp
    """)
    r = profile_env_file(p)
    assert "APP_NAME" in r.string_keys


def test_to_dict_contains_all_fields(tmp_env):
    p = tmp_env("HOST=localhost\n")
    d = profile_env_file(p).to_dict()
    for key in ("path", "total_keys", "empty_keys", "sensitive_keys",
                "url_keys", "int_keys", "bool_keys", "string_keys"):
        assert key in d


def test_empty_file_zero_keys(tmp_env):
    p = tmp_env("")
    r = profile_env_file(p)
    assert r.total_keys == 0
