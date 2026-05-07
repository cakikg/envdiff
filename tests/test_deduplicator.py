"""Tests for envdiff.deduplicator."""
from __future__ import annotations

import pytest
from pathlib import Path

from envdiff.deduplicator import deduplicate_env_file, DeduplicateResult


@pytest.fixture()
def tmp_env(tmp_path: Path) -> Path:
    return tmp_path / ".env"


def _write(p: Path, content: str) -> None:
    p.write_text(content, encoding="utf-8")


def test_no_duplicates_unchanged(tmp_env):
    _write(tmp_env, "FOO=1\nBAR=2\n")
    result = deduplicate_env_file(tmp_env)
    assert not result.changed
    assert result.removed == []


def test_duplicate_key_removed_keeps_last(tmp_env):
    _write(tmp_env, "FOO=first\nBAR=x\nFOO=last\n")
    result = deduplicate_env_file(tmp_env, keep="last")
    assert result.changed
    assert result.removed == ["FOO"]
    content = tmp_env.read_text()
    assert "FOO=last" in content
    assert "FOO=first" not in content


def test_duplicate_key_removed_keeps_first(tmp_env):
    _write(tmp_env, "FOO=first\nBAR=x\nFOO=last\n")
    result = deduplicate_env_file(tmp_env, keep="first")
    assert result.changed
    assert result.removed == ["FOO"]
    content = tmp_env.read_text()
    assert "FOO=first" in content
    assert "FOO=last" not in content


def test_dry_run_does_not_write(tmp_env):
    original = "FOO=1\nFOO=2\n"
    _write(tmp_env, original)
    result = deduplicate_env_file(tmp_env, dry_run=True)
    assert result.changed
    assert tmp_env.read_text() == original  # file untouched


def test_comments_and_blanks_preserved(tmp_env):
    _write(tmp_env, "# comment\nFOO=1\n\nFOO=2\n")
    result = deduplicate_env_file(tmp_env)
    content = tmp_env.read_text()
    assert "# comment" in content
    assert "\n\n" in content


def test_three_duplicates_only_one_kept(tmp_env):
    _write(tmp_env, "KEY=a\nKEY=b\nKEY=c\n")
    result = deduplicate_env_file(tmp_env, keep="last")
    assert len(result.removed) == 2
    assert tmp_env.read_text().count("KEY=") == 1


def test_to_dict_structure(tmp_env):
    _write(tmp_env, "A=1\nA=2\n")
    result = deduplicate_env_file(tmp_env, dry_run=True)
    d = result.to_dict()
    assert "file" in d
    assert "changed" in d
    assert "removed_keys" in d
    assert d["changed"] is True


def test_invalid_keep_raises(tmp_env):
    _write(tmp_env, "A=1\n")
    with pytest.raises(ValueError, match="keep must be"):
        deduplicate_env_file(tmp_env, keep="middle")


def test_lines_in_result_match_written_file(tmp_env):
    _write(tmp_env, "X=1\nX=2\nY=3\n")
    result = deduplicate_env_file(tmp_env, keep="last")
    written = tmp_env.read_text()
    assert "".join(result.lines) == written
