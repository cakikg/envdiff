"""Tests for envdiff.trimmer."""
from __future__ import annotations

import pytest
from pathlib import Path

from envdiff.trimmer import trim_env_file, _trim_line


@pytest.fixture()
def tmp_env(tmp_path: Path):
    def _write(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(content, encoding="utf-8")
        return p
    return _write


# ---------------------------------------------------------------------------
# _trim_line unit tests
# ---------------------------------------------------------------------------

def test_trim_line_plain_value_with_trailing_space():
    assert _trim_line("KEY=value   \n") == "KEY=value\n"


def test_trim_line_plain_value_no_change():
    assert _trim_line("KEY=value\n") == "KEY=value\n"


def test_trim_line_double_quoted_value():
    assert _trim_line('KEY="hello   "\n') == 'KEY="hello"\n'


def test_trim_line_single_quoted_value():
    assert _trim_line("KEY='world  '\n") == "KEY='world'\n"


def test_trim_line_comment_unchanged():
    # Comments should only lose trailing whitespace, not content
    assert _trim_line("# comment   \n") == "# comment\n"


def test_trim_line_blank_line():
    assert _trim_line("   \n") == "\n"


# ---------------------------------------------------------------------------
# trim_env_file integration tests
# ---------------------------------------------------------------------------

def test_clean_file_has_no_changes(tmp_env):
    p = tmp_env("KEY=value\nOTHER=123\n")
    result = trim_env_file(p)
    assert not result.changed
    assert result.changes == []


def test_dirty_file_reports_changes(tmp_env):
    p = tmp_env("KEY=value   \nOTHER=123\n")
    result = trim_env_file(p, dry_run=True)
    assert result.changed
    assert len(result.changes) == 1
    lineno, before, after = result.changes[0]
    assert lineno == 1
    assert before == "KEY=value   \n"
    assert after == "KEY=value\n"


def test_dry_run_does_not_write(tmp_env):
    content = "KEY=value   \n"
    p = tmp_env(content)
    trim_env_file(p, dry_run=True)
    assert p.read_text(encoding="utf-8") == content


def test_writes_file_when_not_dry_run(tmp_env):
    p = tmp_env("KEY=value   \n")
    trim_env_file(p)
    assert p.read_text(encoding="utf-8") == "KEY=value\n"


def test_multiple_dirty_lines(tmp_env):
    p = tmp_env("A=1   \nB=2  \nC=3\n")
    result = trim_env_file(p)
    assert len(result.changes) == 2
    assert p.read_text(encoding="utf-8") == "A=1\nB=2\nC=3\n"


def test_to_dict_structure(tmp_env):
    p = tmp_env("X=hello   \n")
    result = trim_env_file(p, dry_run=True)
    d = result.to_dict()
    assert d["changed"] is True
    assert d["change_count"] == 1
    assert isinstance(d["changes"], list)
    assert d["changes"][0]["line"] == 1
