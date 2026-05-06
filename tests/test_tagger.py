"""Unit tests for envdiff.tagger."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.tagger import (
    TagResult,
    keys_with_label,
    load_tags,
    save_tags,
    tag_key,
    untag_key,
)


@pytest.fixture()
def tmp_env(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY=abc\n")
    return p


def test_load_tags_missing_sidecar_returns_empty(tmp_env: Path) -> None:
    assert load_tags(tmp_env) == {}


def test_save_and_load_round_trip(tmp_env: Path) -> None:
    tags = {"DB_HOST": ["infra", "required"], "SECRET_KEY": ["sensitive"]}
    save_tags(tmp_env, tags)
    loaded = load_tags(tmp_env)
    assert loaded == tags


def test_tag_key_adds_label(tmp_env: Path) -> None:
    result = tag_key(tmp_env, "DB_HOST", "infra")
    assert result.changed
    assert "DB_HOST" in result.added
    assert load_tags(tmp_env)["DB_HOST"] == ["infra"]


def test_tag_key_duplicate_label_is_unchanged(tmp_env: Path) -> None:
    tag_key(tmp_env, "DB_HOST", "infra")
    result = tag_key(tmp_env, "DB_HOST", "infra")
    assert not result.changed
    assert "DB_HOST" in result.unchanged
    assert load_tags(tmp_env)["DB_HOST"] == ["infra"]


def test_tag_key_dry_run_does_not_persist(tmp_env: Path) -> None:
    result = tag_key(tmp_env, "DB_HOST", "infra", dry_run=True)
    assert result.changed
    assert load_tags(tmp_env) == {}


def test_untag_key_removes_specific_label(tmp_env: Path) -> None:
    save_tags(tmp_env, {"DB_HOST": ["infra", "required"]})
    result = untag_key(tmp_env, "DB_HOST", "infra")
    assert result.changed
    assert load_tags(tmp_env)["DB_HOST"] == ["required"]


def test_untag_key_removes_all_labels_when_none(tmp_env: Path) -> None:
    save_tags(tmp_env, {"DB_HOST": ["infra", "required"]})
    result = untag_key(tmp_env, "DB_HOST")
    assert result.changed
    assert "DB_HOST" not in load_tags(tmp_env)


def test_untag_key_missing_key_is_unchanged(tmp_env: Path) -> None:
    result = untag_key(tmp_env, "NONEXISTENT", "infra")
    assert not result.changed
    assert "NONEXISTENT" in result.unchanged


def test_untag_key_dry_run_does_not_persist(tmp_env: Path) -> None:
    save_tags(tmp_env, {"DB_HOST": ["infra"]})
    untag_key(tmp_env, "DB_HOST", "infra", dry_run=True)
    assert load_tags(tmp_env)["DB_HOST"] == ["infra"]


def test_keys_with_label_returns_matching_keys(tmp_env: Path) -> None:
    save_tags(tmp_env, {"DB_HOST": ["infra"], "DB_PORT": ["infra", "required"], "SECRET_KEY": ["sensitive"]})
    result = keys_with_label(tmp_env, "infra")
    assert set(result) == {"DB_HOST", "DB_PORT"}


def test_keys_with_label_no_match_returns_empty(tmp_env: Path) -> None:
    save_tags(tmp_env, {"DB_HOST": ["infra"]})
    assert keys_with_label(tmp_env, "deprecated") == []


def test_tag_result_to_dict(tmp_env: Path) -> None:
    r = TagResult(added=["A"], removed=[], unchanged=["B"])
    d = r.to_dict()
    assert d["added"] == ["A"]
    assert d["changed"] is True
