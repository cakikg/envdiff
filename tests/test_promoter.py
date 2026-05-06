"""Tests for envdiff.promoter."""
from __future__ import annotations

import pytest
from pathlib import Path

from envdiff.promoter import promote_env_file, PromoteResult


@pytest.fixture()
def tmp_env(tmp_path):
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


# ---------------------------------------------------------------------------
# Basic promotion
# ---------------------------------------------------------------------------

def test_adds_missing_key(tmp_env):
    src = _write(tmp_env / "source.env", "FOO=bar\nBAZ=qux\n")
    tgt = _write(tmp_env / "target.env", "EXISTING=1\n")

    result = promote_env_file(src, tgt)

    assert "FOO" in result.added
    assert "BAZ" in result.added
    assert tgt.read_text().__contains__("FOO=bar")


def test_skips_existing_key_by_default(tmp_env):
    src = _write(tmp_env / "source.env", "FOO=new_value\n")
    tgt = _write(tmp_env / "target.env", "FOO=old_value\n")

    result = promote_env_file(src, tgt)

    assert "FOO" in result.skipped
    assert result.added == []
    assert "old_value" in tgt.read_text()


def test_overwrites_existing_key_when_requested(tmp_env):
    src = _write(tmp_env / "source.env", "FOO=new_value\n")
    tgt = _write(tmp_env / "target.env", "FOO=old_value\n")

    result = promote_env_file(src, tgt, overwrite=True)

    assert "FOO" in result.overwritten
    assert "new_value" in tgt.read_text()


# ---------------------------------------------------------------------------
# Key filtering
# ---------------------------------------------------------------------------

def test_promotes_only_specified_keys(tmp_env):
    src = _write(tmp_env / "source.env", "FOO=1\nBAR=2\nBAZ=3\n")
    tgt = tmp_env / "target.env"

    result = promote_env_file(src, tgt, keys=["FOO", "BAZ"])

    assert "FOO" in result.added
    assert "BAZ" in result.added
    assert "BAR" not in result.added
    assert "BAR" not in tgt.read_text()


def test_ignores_key_not_in_source(tmp_env):
    src = _write(tmp_env / "source.env", "FOO=1\n")
    tgt = tmp_env / "target.env"

    result = promote_env_file(src, tgt, keys=["MISSING"])

    assert result.added == []
    assert not tgt.exists() or tgt.read_text() == ""


# ---------------------------------------------------------------------------
# Redaction
# ---------------------------------------------------------------------------

def test_redact_values_writes_empty_value(tmp_env):
    src = _write(tmp_env / "source.env", "SECRET=supersecret\n")
    tgt = tmp_env / "target.env"

    promote_env_file(src, tgt, redact_values=True)

    content = tgt.read_text()
    assert "SECRET=" in content
    assert "supersecret" not in content


# ---------------------------------------------------------------------------
# Dry run
# ---------------------------------------------------------------------------

def test_dry_run_does_not_write(tmp_env):
    src = _write(tmp_env / "source.env", "FOO=bar\n")
    tgt = tmp_env / "target.env"

    result = promote_env_file(src, tgt, dry_run=True)

    assert "FOO" in result.added
    assert not tgt.exists()


# ---------------------------------------------------------------------------
# PromoteResult helpers
# ---------------------------------------------------------------------------

def test_result_changed_false_when_only_skipped():
    r = PromoteResult(skipped=["A"])
    assert not r.changed


def test_result_to_dict_structure():
    r = PromoteResult(added=["A"], skipped=["B"], overwritten=["C"])
    d = r.to_dict()
    assert d["added"] == ["A"]
    assert d["skipped"] == ["B"]
    assert d["overwritten"] == ["C"]
