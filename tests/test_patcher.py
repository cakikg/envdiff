"""Tests for envdiff.patcher."""

from __future__ import annotations

from pathlib import Path

import pytest

from envdiff.differ import unified_value_diff
from envdiff.patcher import patch_env_file


@pytest.fixture()
def tmp_env(tmp_path: Path):
    """Return a helper that writes a .env file and returns its Path."""

    def _write(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")
        return p

    return _write


def _diff(source: dict, target: dict):
    return unified_value_diff(source, target)


# ---------------------------------------------------------------------------
# dry_run behaviour
# ---------------------------------------------------------------------------

def test_dry_run_does_not_write(tmp_env, tmp_path):
    target = tmp_env("target.env", "A=1\n")
    diffs = _diff({"A": "1", "B": "2"}, {"A": "1"})
    report = patch_env_file(target, diffs, dry_run=True)
    # File should be unchanged
    assert target.read_text() == "A=1\n"
    assert "B" in report["added"]


# ---------------------------------------------------------------------------
# Adding missing keys
# ---------------------------------------------------------------------------

def test_adds_missing_key(tmp_env):
    target = tmp_env("target.env", "A=1\n")
    diffs = _diff({"A": "1", "B": "hello"}, {"A": "1"})
    report = patch_env_file(target, diffs)
    content = target.read_text()
    assert "B=hello" in content
    assert "B" in report["added"]


def test_adds_multiple_missing_keys(tmp_env):
    target = tmp_env("target.env", "A=1\n")
    diffs = _diff({"A": "1", "B": "2", "C": "3"}, {"A": "1"})
    report = patch_env_file(target, diffs)
    content = target.read_text()
    assert "B=2" in content
    assert "C=3" in content
    assert set(report["added"]) == {"B", "C"}


def test_patch_block_has_comment_header(tmp_env):
    target = tmp_env("target.env", "A=1\n")
    diffs = _diff({"A": "1", "NEW": "val"}, {"A": "1"})
    patch_env_file(target, diffs)
    assert "# patched by envdiff" in target.read_text()


# ---------------------------------------------------------------------------
# Updating changed keys
# ---------------------------------------------------------------------------

def test_update_changed_rewrites_value(tmp_env):
    target = tmp_env("target.env", "A=old\n")
    diffs = _diff({"A": "new"}, {"A": "old"})
    report = patch_env_file(target, diffs, update_changed=True)
    assert "A=new" in target.read_text()
    assert "A" in report["updated"]


def test_no_update_changed_by_default(tmp_env):
    target = tmp_env("target.env", "A=old\n")
    diffs = _diff({"A": "new"}, {"A": "old"})
    report = patch_env_file(target, diffs, update_changed=False)
    assert "A=old" in target.read_text()
    assert report["updated"] == []


# ---------------------------------------------------------------------------
# Removed keys (keys in target but not in source) are never deleted
# ---------------------------------------------------------------------------

def test_removed_keys_are_skipped(tmp_env):
    target = tmp_env("target.env", "A=1\nEXTRA=keep\n")
    diffs = _diff({"A": "1"}, {"A": "1", "EXTRA": "keep"})
    report = patch_env_file(target, diffs)
    assert "EXTRA=keep" in target.read_text()
    assert "EXTRA" in report["skipped"]


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------

def test_no_diff_leaves_file_unchanged(tmp_env):
    original = "A=1\nB=2\n"
    target = tmp_env("target.env", original)
    diffs = _diff({"A": "1", "B": "2"}, {"A": "1", "B": "2"})
    patch_env_file(target, diffs)
    assert target.read_text() == original
