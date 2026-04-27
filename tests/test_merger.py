"""Tests for envdiff.merger."""

import pytest

from envdiff.merger import merge_conflicts, merge_env_files


ENV_A = {"HOST": "localhost", "PORT": "5432", "DEBUG": "true"}
ENV_B = {"HOST": "prod.example.com", "PORT": "5432", "SECRET": "abc123"}
ENV_C = {"HOST": "staging.example.com", "TIMEOUT": "30"}


def test_merge_first_strategy_keeps_first_value():
    result = merge_env_files({"a": ENV_A, "b": ENV_B}, strategy="first")
    assert result["HOST"] == "localhost"  # from ENV_A


def test_merge_last_strategy_keeps_last_value():
    result = merge_env_files({"a": ENV_A, "b": ENV_B}, strategy="last")
    assert result["HOST"] == "prod.example.com"  # from ENV_B


def test_merge_includes_all_keys():
    result = merge_env_files({"a": ENV_A, "b": ENV_B}, strategy="first")
    assert set(result.keys()) == {"HOST", "PORT", "DEBUG", "SECRET"}


def test_merge_non_conflicting_key_always_present():
    result = merge_env_files({"a": ENV_A, "b": ENV_B}, strategy="first")
    assert result["PORT"] == "5432"
    assert result["DEBUG"] == "true"
    assert result["SECRET"] == "abc123"


def test_merge_error_strategy_raises_on_conflict():
    with pytest.raises(ValueError, match="Conflict"):
        merge_env_files({"a": ENV_A, "b": ENV_B}, strategy="error")


def test_merge_error_strategy_passes_when_no_conflicts():
    env_x = {"ONLY_X": "1"}
    env_y = {"ONLY_Y": "2"}
    result = merge_env_files({"x": env_x, "y": env_y}, strategy="error")
    assert result == {"ONLY_X": "1", "ONLY_Y": "2"}


def test_merge_unknown_strategy_raises():
    with pytest.raises(ValueError, match="Unknown merge strategy"):
        merge_env_files({"a": ENV_A}, strategy="unknown")


def test_merge_empty_envs():
    assert merge_env_files({}) == {}


def test_merge_single_env():
    result = merge_env_files({"a": ENV_A})
    assert result == ENV_A


def test_merge_conflicts_detects_differing_values():
    conflicts = merge_conflicts({"a": ENV_A, "b": ENV_B})
    assert "HOST" in conflicts
    sources = {src for _, _, src in conflicts["HOST"]}
    assert sources == {"a", "b"}


def test_merge_conflicts_ignores_matching_values():
    conflicts = merge_conflicts({"a": ENV_A, "b": ENV_B})
    # PORT is the same in both — should not appear
    assert "PORT" not in conflicts


def test_merge_conflicts_keys_unique_to_one_file_not_flagged():
    conflicts = merge_conflicts({"a": ENV_A, "b": ENV_B})
    assert "DEBUG" not in conflicts
    assert "SECRET" not in conflicts


def test_merge_conflicts_three_files():
    conflicts = merge_conflicts({"a": ENV_A, "b": ENV_B, "c": ENV_C})
    assert "HOST" in conflicts
    values = {v for _, v, _ in conflicts["HOST"]}
    assert values == {"localhost", "prod.example.com", "staging.example.com"}


def test_merge_conflicts_empty_returns_empty():
    assert merge_conflicts({}) == {}
