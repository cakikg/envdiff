"""Tests for envdiff.validator."""

from __future__ import annotations

import pytest

from envdiff.validator import ValidationResult, validate_env


SCHEMA = {
    "PORT": {"required": True, "type": "int"},
    "DEBUG": {"required": False, "type": "bool"},
    "DATABASE_URL": {"required": True, "type": "url"},
    "APP_NAME": {"required": True, "type": "str"},
}


def _valid_env():
    return {
        "PORT": "8080",
        "DEBUG": "true",
        "DATABASE_URL": "https://db.example.com",
        "APP_NAME": "myapp",
    }


def test_valid_env_passes():
    result = validate_env(_valid_env(), SCHEMA)
    assert result.is_valid
    assert not result.missing_required
    assert not result.type_mismatches


def test_missing_required_key():
    env = _valid_env()
    del env["PORT"]
    result = validate_env(env, SCHEMA, file_path=".env.prod")
    assert not result.is_valid
    assert "PORT" in result.missing_required
    assert result.file_path == ".env.prod"


def test_optional_key_missing_is_ok():
    env = _valid_env()
    del env["DEBUG"]
    result = validate_env(env, SCHEMA)
    assert result.is_valid


def test_type_mismatch_int():
    env = {**_valid_env(), "PORT": "not-a-number"}
    result = validate_env(env, SCHEMA)
    assert not result.is_valid
    assert "PORT" in result.type_mismatches
    assert result.type_mismatches["PORT"] == "int"


def test_type_mismatch_bool():
    env = {**_valid_env(), "DEBUG": "maybe"}
    result = validate_env(env, SCHEMA)
    assert "DEBUG" in result.type_mismatches


def test_type_mismatch_url():
    env = {**_valid_env(), "DATABASE_URL": "ftp://bad"}
    result = validate_env(env, SCHEMA)
    assert "DATABASE_URL" in result.type_mismatches


def test_strict_mode_reports_unknown_keys():
    env = {**_valid_env(), "EXTRA_KEY": "surprise"}
    result = validate_env(env, SCHEMA, strict=True)
    assert result.is_valid  # no required missing, no type errors
    assert result.has_warnings
    assert "EXTRA_KEY" in result.unknown_keys


def test_non_strict_mode_ignores_unknown_keys():
    env = {**_valid_env(), "EXTRA_KEY": "surprise"}
    result = validate_env(env, SCHEMA, strict=False)
    assert not result.unknown_keys


def test_validation_result_repr_fields():
    r = ValidationResult(
        file_path=".env",
        missing_required=["FOO"],
        type_mismatches={"BAR": "int"},
    )
    assert not r.is_valid
    assert not r.has_warnings
