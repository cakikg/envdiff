"""Tests for envdiff.core module."""

import pytest
from unittest.mock import mock_open, patch
from envdiff.core import parse_env_file, compare_env_files, compare_multiple


ENV_A = """DB_HOST=localhost
DB_PORT=5432
SECRET=abc123
DEBUG=true
"""

ENV_B = """DB_HOST=prod.example.com
DB_PORT=5432
NEW_KEY=hello
DEBUG=false
"""


def _make_parse(content: str):
    """Helper to parse env content from a string."""
    lines = content.strip().splitlines()
    result = {}
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            result[key.strip()] = value.strip()
    return result


def test_parse_env_file_basic(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\nBAZ=qux\n")
    result = parse_env_file(str(env_file))
    assert result["FOO"] == "bar"
    assert result["BAZ"] == "qux"


def test_parse_env_file_ignores_comments(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("# comment\nFOO=bar\n")
    result = parse_env_file(str(env_file))
    assert "# comment" not in result
    assert result["FOO"] == "bar"


def test_parse_env_file_ignores_blank_lines(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("\nFOO=bar\n\nBAZ=qux\n")
    result = parse_env_file(str(env_file))
    assert len(result) == 2


def test_compare_env_files_missing_keys(tmp_path):
    a = tmp_path / "a.env"
    b = tmp_path / "b.env"
    a.write_text(ENV_A)
    b.write_text(ENV_B)
    diff = compare_env_files(str(a), str(b))
    assert "SECRET" in diff["missing_in_b"]
    assert "NEW_KEY" in diff["missing_in_a"]


def test_compare_env_files_mismatched(tmp_path):
    a = tmp_path / "a.env"
    b = tmp_path / "b.env"
    a.write_text(ENV_A)
    b.write_text(ENV_B)
    diff = compare_env_files(str(a), str(b))
    assert "DB_HOST" in diff["mismatched"]
    assert "DEBUG" in diff["mismatched"]


def test_compare_env_files_matching_keys_not_in_diff(tmp_path):
    a = tmp_path / "a.env"
    b = tmp_path / "b.env"
    a.write_text(ENV_A)
    b.write_text(ENV_B)
    diff = compare_env_files(str(a), str(b))
    assert "DB_PORT" not in diff.get("mismatched", {})
    assert "DB_PORT" not in diff.get("missing_in_a", [])
    assert "DB_PORT" not in diff.get("missing_in_b", [])


def test_compare_multiple_returns_all_pairs(tmp_path):
    files = []
    for name, content in [("a.env", "X=1\n"), ("b.env", "X=2\nY=3\n"), ("c.env", "X=1\n")]:
        f = tmp_path / name
        f.write_text(content)
        files.append(str(f))
    results = compare_multiple(files)
    pairs = [(r["file_a"], r["file_b"]) for r in results]
    assert len(results) == 3  # (a,b), (a,c), (b,c)
