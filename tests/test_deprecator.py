"""Tests for envdiff.deprecator."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.deprecator import check_deprecations, DeprecationReport


@pytest.fixture()
def tmp_env(tmp_path: Path):
    def _write(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(content)
        return p
    return _write


DEPRECATED = {
    "OLD_API_KEY": {"reason": "renamed", "replacement": "API_KEY"},
    "LEGACY_MODE": {"reason": "feature removed"},
}


def test_clean_file_returns_empty_hits(tmp_env):
    path = tmp_env("API_KEY=abc\nDEBUG=true\n")
    report = check_deprecations(path, DEPRECATED)
    assert report.clean
    assert report.hits == []


def test_deprecated_key_detected(tmp_env):
    path = tmp_env("OLD_API_KEY=secret\nDEBUG=true\n")
    report = check_deprecations(path, DEPRECATED)
    assert not report.clean
    assert len(report.hits) == 1
    assert report.hits[0].key == "OLD_API_KEY"


def test_multiple_deprecated_keys_detected(tmp_env):
    path = tmp_env("OLD_API_KEY=x\nLEGACY_MODE=1\n")
    report = check_deprecations(path, DEPRECATED)
    keys = {h.key for h in report.hits}
    assert keys == {"OLD_API_KEY", "LEGACY_MODE"}


def test_reason_stored_correctly(tmp_env):
    path = tmp_env("LEGACY_MODE=on\n")
    report = check_deprecations(path, DEPRECATED)
    assert report.hits[0].reason == "feature removed"


def test_replacement_stored_when_present(tmp_env):
    path = tmp_env("OLD_API_KEY=s\n")
    report = check_deprecations(path, DEPRECATED)
    assert report.hits[0].replacement == "API_KEY"


def test_replacement_none_when_absent(tmp_env):
    path = tmp_env("LEGACY_MODE=1\n")
    report = check_deprecations(path, DEPRECATED)
    assert report.hits[0].replacement is None


def test_total_keys_counted(tmp_env):
    path = tmp_env("A=1\nB=2\nOLD_API_KEY=x\n")
    report = check_deprecations(path, DEPRECATED)
    assert report.total_keys == 3


def test_to_dict_structure(tmp_env):
    path = tmp_env("OLD_API_KEY=s\n")
    report = check_deprecations(path, DEPRECATED)
    d = report.to_dict()
    assert "file" in d
    assert "clean" in d
    assert "hits" in d
    assert d["hits"][0]["key"] == "OLD_API_KEY"


def test_empty_deprecated_dict_always_clean(tmp_env):
    path = tmp_env("OLD_API_KEY=s\nLEGACY_MODE=1\n")
    report = check_deprecations(path, {})
    assert report.clean
