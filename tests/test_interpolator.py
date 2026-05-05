"""Unit tests for envdiff.interpolator."""
import pytest

from envdiff.interpolator import interpolate_env, _refs_in


def test_no_references_returns_unchanged():
    env = {"FOO": "bar", "BAZ": "qux"}
    result = interpolate_env(env)
    assert result.resolved == env
    assert result.ok


def test_simple_brace_reference_resolved():
    env = {"BASE": "/app", "DATA": "${BASE}/data"}
    result = interpolate_env(env)
    assert result.resolved["DATA"] == "/app/data"
    assert result.ok


def test_simple_dollar_reference_resolved():
    env = {"HOST": "localhost", "URL": "http://$HOST:5432"}
    result = interpolate_env(env)
    assert result.resolved["URL"] == "http://localhost:5432"
    assert result.ok


def test_chained_references_resolved():
    env = {"A": "hello", "B": "${A} world", "C": "${B}!"}
    result = interpolate_env(env)
    assert result.resolved["C"] == "hello world!"


def test_external_variable_used_as_fallback():
    env = {"GREETING": "${SALUTATION} world"}
    result = interpolate_env(env, external={"SALUTATION": "hi"})
    assert result.resolved["GREETING"] == "hi world"
    assert result.ok


def test_missing_reference_reported():
    env = {"FOO": "${MISSING_VAR}"}
    result = interpolate_env(env)
    assert "FOO" in result.unresolved
    assert "MISSING_VAR" in result.unresolved["FOO"]
    assert not result.ok


def test_multiple_missing_refs_all_reported():
    env = {"FOO": "${A}_${B}"}
    result = interpolate_env(env)
    assert set(result.unresolved["FOO"]) == {"A", "B"}


def test_refs_in_helper_finds_brace_and_bare():
    refs = _refs_in("${FOO} and $BAR end")
    assert refs == ["FOO", "BAR"]


def test_refs_in_empty_string():
    assert _refs_in("") == []


def test_external_key_not_included_in_resolved():
    """Keys from *external* must not appear in result.resolved."""
    env = {"GREETING": "${SALUTATION}"}
    result = interpolate_env(env, external={"SALUTATION": "hey"})
    assert "SALUTATION" not in result.resolved
    assert result.resolved["GREETING"] == "hey"
