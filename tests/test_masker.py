"""Tests for envdiff.masker."""
from __future__ import annotations

import pytest
from pathlib import Path

from envdiff.masker import mask_env_file, MaskResult, _DEFAULT_MASK


@pytest.fixture()
def tmp_env(tmp_path: Path):
    def _write(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(content)
        return p
    return _write


def test_sensitive_key_is_masked(tmp_env):
    p = tmp_env("SECRET_KEY=supersecret\nAPP_NAME=myapp\n")
    result = mask_env_file(p)
    assert "SECRET_KEY=***" in result.content()
    assert "APP_NAME=myapp" in result.content()


def test_masked_keys_list_populated(tmp_env):
    p = tmp_env("API_KEY=abc123\nDEBUG=true\n")
    result = mask_env_file(p)
    assert "API_KEY" in result.masked_keys
    assert "DEBUG" not in result.masked_keys


def test_changed_is_true_when_keys_masked(tmp_env):
    p = tmp_env("PASSWORD=hunter2\n")
    result = mask_env_file(p)
    assert result.changed is True


def test_changed_is_false_when_no_sensitive_keys(tmp_env):
    p = tmp_env("APP_ENV=production\nPORT=8080\n")
    result = mask_env_file(p)
    assert result.changed is False


def test_custom_mask_string(tmp_env):
    p = tmp_env("SECRET=abc\n")
    result = mask_env_file(p, mask="<REDACTED>")
    assert "SECRET=<REDACTED>" in result.content()


def test_extra_patterns_treated_as_sensitive(tmp_env):
    p = tmp_env("MY_CUSTOM_TOKEN=xyz\nNAME=alice\n")
    result = mask_env_file(p, extra_patterns=["*TOKEN*"])
    assert "MY_CUSTOM_TOKEN" in result.masked_keys
    assert "NAME" not in result.masked_keys


def test_write_flag_persists_changes(tmp_env):
    p = tmp_env("DB_PASSWORD=secret\n")
    mask_env_file(p, write=True)
    content = p.read_text()
    assert "DB_PASSWORD=***" in content
    assert "secret" not in content


def test_dry_run_does_not_write(tmp_env):
    original = "DB_PASSWORD=secret\n"
    p = tmp_env(original)
    mask_env_file(p, write=False)
    assert p.read_text() == original


def test_comments_preserved(tmp_env):
    p = tmp_env("# header comment\nSECRET=abc\nAPP=x\n")
    result = mask_env_file(p)
    assert "# header comment" in result.content()


def test_to_dict_structure(tmp_env):
    p = tmp_env("TOKEN=abc\n")
    result = mask_env_file(p)
    d = result.to_dict()
    assert "file" in d
    assert "masked_keys" in d
    assert "changed" in d


def test_blank_lines_preserved(tmp_env):
    p = tmp_env("KEY=value\n\nOTHER=x\n")
    result = mask_env_file(p)
    lines = result.lines
    assert "" in lines
