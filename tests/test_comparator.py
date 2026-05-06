"""Unit tests for envdiff.comparator."""
from __future__ import annotations

from pathlib import Path

import pytest

from envdiff.comparator import CompareReport, KeyStatus, compare_envs


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# KeyStatus
# ---------------------------------------------------------------------------

def test_key_status_consistent_when_same_value():
    ks = KeyStatus(key="FOO", values={"dev": "bar", "prod": "bar"})
    assert ks.is_consistent is True


def test_key_status_inconsistent_when_different_values():
    ks = KeyStatus(key="FOO", values={"dev": "bar", "prod": "baz"})
    assert ks.is_consistent is False


def test_key_status_consistent_when_only_one_env_has_key():
    ks = KeyStatus(key="FOO", values={"dev": "bar", "prod": None})
    # only one present value — consistent by definition
    assert ks.is_consistent is True


def test_key_status_missing_in_lists_absent_envs():
    ks = KeyStatus(key="FOO", values={"dev": "bar", "prod": None, "stg": None})
    assert set(ks.missing_in) == {"prod", "stg"}


def test_key_status_present_in_lists_present_envs():
    ks = KeyStatus(key="FOO", values={"dev": "bar", "prod": None})
    assert ks.present_in == ["dev"]


def test_key_status_to_dict_keys():
    ks = KeyStatus(key="FOO", values={"dev": "bar"})
    d = ks.to_dict()
    assert set(d.keys()) == {"key", "consistent", "missing_in", "values"}


# ---------------------------------------------------------------------------
# compare_envs
# ---------------------------------------------------------------------------

def test_compare_identical_files_all_ok(tmp_path):
    a = _write(tmp_path, "a.env", "FOO=1\nBAR=2\n")
    b = _write(tmp_path, "b.env", "FOO=1\nBAR=2\n")
    report = compare_envs([a, b])
    assert report.all_ok is True


def test_compare_missing_key_detected(tmp_path):
    a = _write(tmp_path, "a.env", "FOO=1\nBAR=2\n")
    b = _write(tmp_path, "b.env", "FOO=1\n")
    report = compare_envs([a, b])
    assert report.all_ok is False
    missing = {s.key for s in report.missing_keys}
    assert "BAR" in missing


def test_compare_value_mismatch_detected(tmp_path):
    a = _write(tmp_path, "a.env", "FOO=hello\n")
    b = _write(tmp_path, "b.env", "FOO=world\n")
    report = compare_envs([a, b])
    assert len(report.inconsistent_keys) == 1
    assert report.inconsistent_keys[0].key == "FOO"


def test_compare_uses_custom_names(tmp_path):
    a = _write(tmp_path, "a.env", "FOO=1\n")
    b = _write(tmp_path, "b.env", "FOO=2\n")
    report = compare_envs([a, b], names=["dev", "prod"])
    assert report.env_names == ["dev", "prod"]


def test_compare_raises_on_name_length_mismatch(tmp_path):
    a = _write(tmp_path, "a.env", "FOO=1\n")
    b = _write(tmp_path, "b.env", "FOO=2\n")
    with pytest.raises(ValueError):
        compare_envs([a, b], names=["only_one"])


def test_compare_report_to_dict_structure(tmp_path):
    a = _write(tmp_path, "a.env", "FOO=1\n")
    b = _write(tmp_path, "b.env", "FOO=1\n")
    d = compare_envs([a, b]).to_dict()
    assert "envs" in d
    assert "all_ok" in d
    assert "keys" in d
