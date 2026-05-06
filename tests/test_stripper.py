"""Tests for envdiff.stripper."""
from __future__ import annotations

import pytest
from pathlib import Path

from envdiff.stripper import strip_env_file, StripResult


@pytest.fixture()
def tmp_env(tmp_path: Path):
    def _write(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(content, encoding="utf-8")
        return p

    return _write


def test_strip_removes_comments(tmp_env):
    p = tmp_env("# a comment\nKEY=value\n")
    result = strip_env_file(p)
    assert result.removed_comments == 1
    assert "# a comment" not in result.content
    assert "KEY=value" in result.content


def test_strip_removes_blank_lines(tmp_env):
    p = tmp_env("KEY=value\n\n   \nOTHER=x\n")
    result = strip_env_file(p)
    assert result.removed_blanks == 2
    assert result.stripped_lines == 2


def test_strip_keeps_inline_comments_on_assignment(tmp_env):
    """Lines that are assignments should never be stripped even if they
    contain a # character inside the value."""
    p = tmp_env("KEY=val#ue\n")
    result = strip_env_file(p)
    assert result.removed_comments == 0
    assert "KEY=val#ue" in result.content


def test_strip_changed_flag_true_when_lines_removed(tmp_env):
    p = tmp_env("# comment\nKEY=v\n")
    result = strip_env_file(p)
    assert result.changed is True


def test_strip_changed_flag_false_when_nothing_removed(tmp_env):
    p = tmp_env("KEY=v\nOTHER=x\n")
    result = strip_env_file(p)
    assert result.changed is False


def test_strip_does_not_write_by_default(tmp_env):
    p = tmp_env("# comment\nKEY=value\n")
    original = p.read_text()
    strip_env_file(p, write=False)
    assert p.read_text() == original


def test_strip_writes_when_requested(tmp_env):
    p = tmp_env("# comment\nKEY=value\n")
    strip_env_file(p, write=True)
    assert "# comment" not in p.read_text()
    assert "KEY=value" in p.read_text()


def test_strip_keep_comments_option(tmp_env):
    p = tmp_env("# comment\nKEY=value\n\n")
    result = strip_env_file(p, remove_comments=False, remove_blanks=True)
    assert result.removed_comments == 0
    assert result.removed_blanks == 1
    assert "# comment" in result.content


def test_strip_keep_blanks_option(tmp_env):
    p = tmp_env("# comment\nKEY=value\n\n")
    result = strip_env_file(p, remove_comments=True, remove_blanks=False)
    assert result.removed_comments == 1
    assert result.removed_blanks == 0


def test_to_dict_keys(tmp_env):
    p = tmp_env("# c\nKEY=v\n")
    d = strip_env_file(p).to_dict()
    assert set(d.keys()) == {
        "file",
        "original_lines",
        "stripped_lines",
        "removed_comments",
        "removed_blanks",
        "changed",
    }


def test_empty_file_returns_empty_content(tmp_env):
    p = tmp_env("")
    result = strip_env_file(p)
    assert result.content == ""
    assert result.changed is False
