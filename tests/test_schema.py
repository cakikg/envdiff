"""Tests for envdiff.schema."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.schema import load_schema, schema_from_env_file


def test_load_schema_json(tmp_path: Path):
    schema = {
        "PORT": {"required": True, "type": "int"},
        "SECRET": {"required": True, "type": "str"},
    }
    schema_file = tmp_path / "schema.json"
    schema_file.write_text(json.dumps(schema))

    loaded = load_schema(schema_file)
    assert loaded == schema


def test_load_schema_file_not_found(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_schema(tmp_path / "missing.json")


def test_load_schema_unsupported_extension(tmp_path: Path):
    bad_file = tmp_path / "schema.yaml"
    bad_file.write_text("PORT: {}")
    with pytest.raises(ValueError, match="Unsupported schema format"):
        load_schema(bad_file)


def test_load_schema_invalid_json(tmp_path: Path):
    bad_file = tmp_path / "schema.json"
    bad_file.write_text("not-json")
    with pytest.raises(Exception):
        load_schema(bad_file)


def test_load_schema_non_object_json(tmp_path: Path):
    bad_file = tmp_path / "schema.json"
    bad_file.write_text(json.dumps(["PORT", "SECRET"]))
    with pytest.raises(ValueError, match="top-level object"):
        load_schema(bad_file)


def test_schema_from_env_file():
    env = {"PORT": "8080", "DEBUG": "true", "APP": "myapp"}
    schema = schema_from_env_file(env)
    assert set(schema.keys()) == {"PORT", "DEBUG", "APP"}
    for key, constraints in schema.items():
        assert constraints["required"] is True
        assert constraints["type"] == "str"


def test_schema_from_empty_env():
    schema = schema_from_env_file({})
    assert schema == {}
