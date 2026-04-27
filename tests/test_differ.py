"""Tests for envdiff.differ module."""

from __future__ import annotations

import pytest

from envdiff.differ import ValueDiff, build_value_diffs, summarise_value_diffs


ENV_A = {"KEY1": "alpha", "KEY2": "shared", "ONLY_A": "gone"}
ENV_B = {"KEY1": "beta", "KEY2": "shared", "ONLY_B": "new"}


# ---------------------------------------------------------------------------
# build_value_diffs
# ---------------------------------------------------------------------------

def test_no_diff_for_identical_envs():
    env = {"A": "1", "B": "2"}
    assert build_value_diffs(env, env) == []


def test_detects_added_key():
    diffs = build_value_diffs({}, {"NEW": "val"})
    assert len(diffs) == 1
    assert diffs[0].is_added
    assert diffs[0].key == "NEW"


def test_detects_removed_key():
    diffs = build_value_diffs({"OLD": "val"}, {})
    assert len(diffs) == 1
    assert diffs[0].is_removed
    assert diffs[0].key == "OLD"


def test_detects_changed_key():
    diffs = build_value_diffs({"K": "v1"}, {"K": "v2"})
    assert len(diffs) == 1
    assert diffs[0].is_changed


def test_skips_unchanged_keys():
    diffs = build_value_diffs(ENV_A, ENV_B)
    keys = {d.key for d in diffs}
    assert "KEY2" not in keys


def test_returns_all_changed_keys():
    diffs = build_value_diffs(ENV_A, ENV_B)
    keys = {d.key for d in diffs}
    assert keys == {"KEY1", "ONLY_A", "ONLY_B"}


def test_values_redacted_by_default():
    diffs = build_value_diffs({"K": "secret"}, {"K": "other"})
    assert diffs[0].old_value == "***"
    assert diffs[0].new_value == "***"


def test_values_shown_when_requested():
    diffs = build_value_diffs({"K": "v1"}, {"K": "v2"}, show_values=True)
    assert diffs[0].old_value == "v1"
    assert diffs[0].new_value == "v2"


def test_unified_lines_populated_when_show_values():
    diffs = build_value_diffs({"K": "v1"}, {"K": "v2"}, show_values=True)
    assert any(line.startswith("-") or line.startswith("+") for line in diffs[0].unified_lines)


def test_unified_lines_empty_without_show_values():
    diffs = build_value_diffs({"K": "v1"}, {"K": "v2"})
    assert diffs[0].unified_lines == []


# ---------------------------------------------------------------------------
# summarise_value_diffs
# ---------------------------------------------------------------------------

def test_summarise_counts():
    diffs = build_value_diffs(ENV_A, ENV_B)
    summary = summarise_value_diffs(diffs)
    assert summary["added"] == 1
    assert summary["removed"] == 1
    assert summary["changed"] == 1


def test_summarise_empty():
    summary = summarise_value_diffs([])
    assert summary == {"added": 0, "removed": 0, "changed": 0}
