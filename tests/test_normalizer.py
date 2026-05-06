"""Tests for envdiff.normalizer."""
from __future__ import annotations

import pytest
from pathlib import Path

from envdiff.normalizer import normalize_env_file, _normalize_value


@pytest.fixture()
def tmp_env(tmp_path: Path):
    def _write(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(content, encoding="utf-8")
        return p
    return _write


# ---------------------------------------------------------------------------
# _normalize_value unit tests
# ---------------------------------------------------------------------------

def test_normalize_value_strips_double_quotes():
    assert _normalize_value('"hello"') == "hello"


def test_normalize_value_strips_single_quotes():
    assert _normalize_value("'world'") == "world"


def test_normalize_value_no_quotes_unchanged():
    assert _normalize_value("plain") == "plain"


def test_normalize_value_bool_true_variants():
    for v in ("True", "TRUE", "yes", "YES", "1", "on", "ON"):
        assert _normalize_value(v) == "true", f"expected 'true' for {v!r}"


def test_normalize_value_bool_false_variants():
    for v in ("False", "FALSE", "no", "NO", "0", "off", "OFF"):
        assert _normalize_value(v) == "false", f"expected 'false' for {v!r}"


# ---------------------------------------------------------------------------
# normalize_env_file tests
# ---------------------------------------------------------------------------

def test_no_change_for_clean_file(tmp_env):
    path = tmp_env("KEY=value\nOTHER=123\n")
    result = normalize_env_file(path)
    assert not result.changed
    assert result.changes == []


def test_detects_quoted_value(tmp_env):
    path = tmp_env('KEY="hello"\n')
    result = normalize_env_file(path)
    assert result.changed
    assert any("hello" in after for _, _, after in result.changes)


def test_detects_bool_normalization(tmp_env):
    path = tmp_env("ENABLED=True\nDEBUG=YES\n")
    result = normalize_env_file(path)
    assert result.changed
    assert len(result.changes) == 2


def test_comments_and_blanks_untouched(tmp_env):
    content = "# comment\n\nKEY=value\n"
    path = tmp_env(content)
    result = normalize_env_file(path)
    assert not result.changed


def test_dry_run_does_not_write(tmp_env):
    path = tmp_env('KEY="quoted"\n')
    result = normalize_env_file(path, write=False)
    assert result.changed
    # file must remain unchanged
    assert path.read_text(encoding="utf-8") == 'KEY="quoted"\n'


def test_write_updates_file(tmp_env):
    path = tmp_env('KEY="quoted"\n')
    result = normalize_env_file(path, write=True)
    assert result.changed
    assert path.read_text(encoding="utf-8") == "KEY=quoted\n"


def test_to_dict_structure(tmp_env):
    path = tmp_env('FLAG=True\n')
    result = normalize_env_file(path)
    d = result.to_dict()
    assert d["changed"] is True
    assert isinstance(d["changes"], list)
    assert d["changes"][0]["line"] == 1
