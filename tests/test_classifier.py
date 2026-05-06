"""Tests for envdiff.classifier."""
from __future__ import annotations

import os
import tempfile
import pytest

from envdiff.classifier import _infer_type, classify_env_file


# ---------------------------------------------------------------------------
# unit: _infer_type
# ---------------------------------------------------------------------------

def test_infer_bool_true():
    assert _infer_type("true") == "bool"

def test_infer_bool_false():
    assert _infer_type("False") == "bool"

def test_infer_int():
    assert _infer_type("42") == "int"

def test_infer_negative_int():
    assert _infer_type("-7") == "int"

def test_infer_float():
    assert _infer_type("3.14") == "float"

def test_infer_url_https():
    assert _infer_type("https://example.com") == "url"

def test_infer_url_postgres():
    assert _infer_type("postgres://user:pass@localhost/db") == "url"

def test_infer_empty():
    assert _infer_type("") == "empty"

def test_infer_plain_string():
    assert _infer_type("hello-world") == "string"


# ---------------------------------------------------------------------------
# integration: classify_env_file
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_env(tmp_path):
    def _write(content: str):
        p = tmp_path / ".env"
        p.write_text(content)
        return str(p)
    return _write


def test_classify_groups_by_type(tmp_env):
    path = tmp_env(
        "PORT=8080\n"
        "DEBUG=true\n"
        "APP_NAME=myapp\n"
        "DATABASE_URL=postgres://localhost/db\n"
    )
    report = classify_env_file(path)
    assert "PORT" in report.by_type["int"]
    assert "DEBUG" in report.by_type["bool"]
    assert "APP_NAME" in report.by_type["string"]
    assert "DATABASE_URL" in report.by_type["url"]


def test_classify_sensitive_tier(tmp_env):
    path = tmp_env("SECRET_KEY=abc123\nAPI_TOKEN=xyz\n")
    report = classify_env_file(path)
    assert "SECRET_KEY" in report.by_tier["sensitive"]
    assert "API_TOKEN" in report.by_tier["sensitive"]


def test_classify_connection_tier(tmp_env):
    path = tmp_env("DB_URL=postgres://localhost/test\n")
    report = classify_env_file(path)
    assert "DB_URL" in report.by_tier["connection"]


def test_classify_config_tier(tmp_env):
    path = tmp_env("MAX_RETRIES=3\nFEATURE_FLAG=true\n")
    report = classify_env_file(path)
    assert "MAX_RETRIES" in report.by_tier["config"]
    assert "FEATURE_FLAG" in report.by_tier["config"]


def test_to_dict_structure(tmp_env):
    path = tmp_env("FOO=bar\n")
    d = classify_env_file(path).to_dict()
    assert "file" in d
    assert "by_type" in d
    assert "by_tier" in d


def test_empty_file_returns_empty_buckets(tmp_env):
    path = tmp_env("")
    report = classify_env_file(path)
    assert report.by_type == {}
    assert report.by_tier == {}
