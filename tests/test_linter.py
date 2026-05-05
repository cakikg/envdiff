"""Tests for envdiff.linter."""
import textwrap
from pathlib import Path

import pytest

from envdiff.linter import lint_env_file


@pytest.fixture()
def tmp_env(tmp_path):
    def _write(content: str) -> str:
        p = tmp_path / ".env"
        p.write_text(textwrap.dedent(content))
        return str(p)
    return _write


def test_clean_file_has_no_issues(tmp_env):
    path = tmp_env("""
        APP_NAME=myapp
        PORT=8080
        DEBUG=false
    """)
    result = lint_env_file(path)
    assert result.ok()
    assert not result.issues


def test_duplicate_key_is_error(tmp_env):
    path = tmp_env("""
        KEY=first
        KEY=second
    """)
    result = lint_env_file(path)
    assert not result.ok()
    errors = [i for i in result.issues if i.severity == "error"]
    assert any("Duplicate" in i.message for i in errors)


def test_missing_equals_is_error(tmp_env):
    path = tmp_env("""
        BADLINE
        GOOD=ok
    """)
    result = lint_env_file(path)
    assert not result.ok()
    assert any("not a valid" in i.message for i in result.issues)


def test_blank_lines_and_comments_ignored(tmp_env):
    path = tmp_env("""
        # This is a comment

        FOO=bar
    """)
    result = lint_env_file(path)
    assert result.ok()
    assert not result.issues


def test_key_with_leading_whitespace_is_warning(tmp_env):
    path = tmp_env(" SPACED=value\n")
    result = lint_env_file(path)
    warnings = [i for i in result.issues if i.severity == "warning"]
    assert any("whitespace" in i.message for i in warnings)


def test_unquoted_value_trailing_space_is_warning(tmp_env):
    path = tmp_env("KEY=value   \n")
    result = lint_env_file(path)
    warnings = [i for i in result.issues if i.severity == "warning"]
    assert any("whitespace" in i.message for i in warnings)


def test_invalid_key_characters_warning(tmp_env):
    path = tmp_env("my-key=value\n")
    result = lint_env_file(path)
    warnings = [i for i in result.issues if i.severity == "warning"]
    assert any("invalid characters" in i.message for i in warnings)


def test_file_not_found_raises():
    with pytest.raises(FileNotFoundError):
        lint_env_file("/nonexistent/.env")


def test_ok_reflects_only_errors(tmp_env):
    """A file with only warnings should still be considered ok."""
    path = tmp_env("my-key=value\n")
    result = lint_env_file(path)
    assert result.ok()
    assert result.has_warnings()


def test_issue_line_numbers_are_reported(tmp_env):
    """Each issue should carry the 1-based line number where it was found."""
    path = tmp_env("""
        GOOD=ok
        BADLINE
        ALSO_GOOD=yes
    """)
    result = lint_env_file(path)
    bad_issues = [
        i for i in result.issues if "not a valid" in i.message
    ]
    assert bad_issues, "Expected at least one 'not a valid' issue"
    assert all(hasattr(i, "line") and i.line > 0 for i in bad_issues)
