"""Tests for envdiff.sorter."""

from __future__ import annotations

import pytest

from envdiff.sorter import sort_env_file


@pytest.fixture()
def tmp_env(tmp_path):
    def _write(content: str):
        p = tmp_path / ".env"
        p.write_text(content, encoding="utf-8")
        return p
    return _write


def test_sort_basic_alphabetical(tmp_env):
    p = tmp_env("ZEBRA=1\nAPPLE=2\nMIDDLE=3\n")
    result = sort_env_file(p)
    keys = [line.split("=")[0] for line in result.splitlines() if "=" in line]
    assert keys == ["APPLE", "MIDDLE", "ZEBRA"]


def test_sort_reverse(tmp_env):
    p = tmp_env("APPLE=1\nZEBRA=2\nMIDDLE=3\n")
    result = sort_env_file(p, reverse=True)
    keys = [line.split("=")[0] for line in result.splitlines() if "=" in line]
    assert keys == ["ZEBRA", "MIDDLE", "APPLE"]


def test_sort_writes_file(tmp_env):
    p = tmp_env("Z=1\nA=2\n")
    sort_env_file(p)
    written = p.read_text(encoding="utf-8")
    keys = [line.split("=")[0] for line in written.splitlines() if "=" in line]
    assert keys == ["A", "Z"]


def test_dry_run_does_not_write(tmp_env):
    original = "Z=1\nA=2\n"
    p = tmp_env(original)
    sort_env_file(p, dry_run=True)
    assert p.read_text(encoding="utf-8") == original


def test_dry_run_returns_sorted_text(tmp_env):
    p = tmp_env("Z=1\nA=2\n")
    result = sort_env_file(p, dry_run=True)
    keys = [line.split("=")[0] for line in result.splitlines() if "=" in line]
    assert keys == ["A", "Z"]


def test_comments_attached_to_key_move_with_it(tmp_env):
    content = "# zebra comment\nZEBRA=1\n# apple comment\nAPPLE=2\n"
    p = tmp_env(content)
    result = sort_env_file(p, group_comments=True)
    lines = result.splitlines()
    apple_idx = next(i for i, l in enumerate(lines) if l.startswith("APPLE"))
    zebra_idx = next(i for i, l in enumerate(lines) if l.startswith("ZEBRA"))
    assert apple_idx < zebra_idx
    # comment should appear directly before APPLE
    assert lines[apple_idx - 1] == "# apple comment"


def test_blank_lines_preserved_at_top(tmp_env):
    content = "\n# header\nZEBRA=1\nAPPLE=2\n"
    p = tmp_env(content)
    result = sort_env_file(p)
    assert result.startswith("\n")


def test_already_sorted_unchanged(tmp_env):
    content = "ALPHA=1\nBETA=2\nGAMMA=3\n"
    p = tmp_env(content)
    result = sort_env_file(p, dry_run=True)
    assert result == content


def test_single_key_unchanged(tmp_env):
    content = "ONLY=value\n"
    p = tmp_env(content)
    result = sort_env_file(p, dry_run=True)
    assert result == content


def test_case_insensitive_sort(tmp_env):
    p = tmp_env("b_KEY=1\nA_KEY=2\n")
    result = sort_env_file(p, dry_run=True)
    keys = [line.split("=")[0] for line in result.splitlines() if "=" in line]
    assert keys == ["A_KEY", "b_KEY"]
