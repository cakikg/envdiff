"""Tests for envdiff.sanitizer."""
from __future__ import annotations

import pytest
from pathlib import Path

from envdiff.sanitizer import sanitize_env_file, _PLACEHOLDER


@pytest.fixture
def tmp_env(tmp_path):
    return tmp_path / ".env"


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def test_sensitive_key_is_replaced(tmp_env):
    _write(tmp_env, "SECRET_KEY=supersecret\nAPP_NAME=myapp\n")
    result = sanitize_env_file(tmp_env)
    assert "SECRET_KEY" in result.sanitized_keys
    assert "APP_NAME" not in result.sanitized_keys


def test_placeholder_appears_in_lines(tmp_env):
    _write(tmp_env, "DB_PASSWORD=hunter2\n")
    result = sanitize_env_file(tmp_env, placeholder="***")
    assert any("DB_PASSWORD=***" in l for l in result.lines)


def test_changed_false_for_clean_file(tmp_env):
    _write(tmp_env, "APP_NAME=myapp\nDEBUG=true\n")
    result = sanitize_env_file(tmp_env)
    assert not result.changed


def test_changed_true_when_keys_sanitized(tmp_env):
    _write(tmp_env, "API_KEY=abc123\n")
    result = sanitize_env_file(tmp_env)
    assert result.changed


def test_write_flag_updates_file(tmp_env):
    _write(tmp_env, "TOKEN=mytoken\nHOST=localhost\n")
    sanitize_env_file(tmp_env, write=True)
    content = tmp_env.read_text(encoding="utf-8")
    assert _PLACEHOLDER in content
    assert "mytoken" not in content


def test_write_false_does_not_modify_file(tmp_env):
    original = "TOKEN=mytoken\n"
    _write(tmp_env, original)
    sanitize_env_file(tmp_env, write=False)
    assert tmp_env.read_text(encoding="utf-8") == original


def test_comments_preserved(tmp_env):
    _write(tmp_env, "# This is a comment\nSECRET=x\n")
    result = sanitize_env_file(tmp_env)
    assert result.lines[0] == "# This is a comment"


def test_blank_lines_preserved(tmp_env):
    _write(tmp_env, "\nSECRET=x\n\n")
    result = sanitize_env_file(tmp_env)
    assert result.lines[0] == ""


def test_extra_patterns_respected(tmp_env):
    _write(tmp_env, "MY_CUSTOM_CRED=value\n")
    result = sanitize_env_file(tmp_env, extra_patterns=["custom_cred"])
    assert "MY_CUSTOM_CRED" in result.sanitized_keys


def test_to_dict_structure(tmp_env):
    _write(tmp_env, "API_SECRET=abc\n")
    d = sanitize_env_file(tmp_env).to_dict()
    assert "file" in d
    assert "changed" in d
    assert "sanitized_keys" in d


def test_content_method_returns_string(tmp_env):
    _write(tmp_env, "APP=x\n")
    result = sanitize_env_file(tmp_env)
    assert isinstance(result.content(), str)
