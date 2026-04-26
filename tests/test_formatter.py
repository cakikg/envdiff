"""Tests for envdiff.formatter module."""

import json
import pytest
from envdiff.formatter import format_table, format_json, format_summary


SAMPLE_DIFF = {
    "missing_in_b": ["SECRET_KEY"],
    "missing_in_a": ["NEW_FEATURE_FLAG"],
    "mismatched": {
        "DATABASE_URL": {
            "a": "postgres://localhost/dev",
            "b": "postgres://prod-host/prod",
        }
    },
    "values_a": {"SECRET_KEY": "abc123"},
    "values_b": {"NEW_FEATURE_FLAG": "true"},
}

EMPTY_DIFF = {
    "missing_in_b": [],
    "missing_in_a": [],
    "mismatched": {},
}


def test_format_table_contains_keys():
    result = format_table(SAMPLE_DIFF, "dev.env", "prod.env")
    assert "SECRET_KEY" in result
    assert "NEW_FEATURE_FLAG" in result
    assert "DATABASE_URL" in result


def test_format_table_status_labels():
    result = format_table(SAMPLE_DIFF, "dev.env", "prod.env")
    assert "MISSING" in result
    assert "ADDED" in result
    assert "MISMATCH" in result


def test_format_table_hides_values_by_default():
    result = format_table(SAMPLE_DIFF, "dev.env", "prod.env")
    assert "abc123" not in result
    assert "postgres://" not in result
    assert "***" in result


def test_format_table_shows_values_when_requested():
    result = format_table(SAMPLE_DIFF, "dev.env", "prod.env", show_values=True)
    assert "postgres://localhost/dev" in result
    assert "postgres://prod-host/prod" in result


def test_format_table_empty_diff():
    result = format_table(EMPTY_DIFF, "a.env", "b.env")
    assert "No differences found" in result


def test_format_json_structure():
    result = format_json(SAMPLE_DIFF, "dev.env", "prod.env")
    data = json.loads(result)
    assert data["files"]["a"] == "dev.env"
    assert data["files"]["b"] == "prod.env"
    assert "SECRET_KEY" in data["missing_in_b"]
    assert "NEW_FEATURE_FLAG" in data["missing_in_a"]
    assert "DATABASE_URL" in data["mismatched"]


def test_format_json_hides_values_by_default():
    result = format_json(SAMPLE_DIFF, "dev.env", "prod.env")
    data = json.loads(result)
    assert data["mismatched"]["DATABASE_URL"]["a"] == "***"


def test_format_json_shows_values():
    result = format_json(SAMPLE_DIFF, "dev.env", "prod.env", show_values=True)
    data = json.loads(result)
    assert data["mismatched"]["DATABASE_URL"]["a"] == "postgres://localhost/dev"


def test_format_summary_with_diffs():
    result = format_summary(SAMPLE_DIFF)
    assert "3 difference(s)" in result
    assert "1 missing in B" in result
    assert "1 missing in A" in result
    assert "1 mismatched" in result


def test_format_summary_no_diffs():
    result = format_summary(EMPTY_DIFF)
    assert result == "Files are identical."
