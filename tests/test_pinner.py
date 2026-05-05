"""Tests for envdiff.pinner."""
import json
import pytest
from pathlib import Path

from envdiff.pinner import (
    DriftReport,
    _checksum,
    detect_drift,
    load_pins,
    pin_env,
)


@pytest.fixture
def tmp_lock(tmp_path):
    return tmp_path / ".env.lock"


ENV = {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET": "abc123"}


def test_pin_creates_file(tmp_lock):
    pin_env(ENV, tmp_lock)
    assert tmp_lock.exists()


def test_pin_round_trips_keys(tmp_lock):
    pin_env(ENV, tmp_lock)
    pins = load_pins(tmp_lock)
    assert set(pins.keys()) == set(ENV.keys())


def test_pin_stores_checksums_not_plaintext(tmp_lock):
    pin_env(ENV, tmp_lock)
    raw = tmp_lock.read_text()
    for v in ENV.values():
        assert v not in raw


def test_pin_checksum_matches_sha256(tmp_lock):
    pin_env(ENV, tmp_lock)
    pins = load_pins(tmp_lock)
    assert pins["DB_HOST"] == _checksum("localhost")


def test_load_pins_raises_if_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_pins(tmp_path / "nonexistent.lock")


def test_no_drift_when_env_unchanged(tmp_lock):
    pin_env(ENV, tmp_lock)
    report = detect_drift(ENV, tmp_lock)
    assert report.clean


def test_drift_detects_added_key(tmp_lock):
    pin_env(ENV, tmp_lock)
    new_env = {**ENV, "NEW_KEY": "value"}
    report = detect_drift(new_env, tmp_lock)
    assert "NEW_KEY" in report.added
    assert report.clean is False


def test_drift_detects_removed_key(tmp_lock):
    pin_env(ENV, tmp_lock)
    reduced = {k: v for k, v in ENV.items() if k != "SECRET"}
    report = detect_drift(reduced, tmp_lock)
    assert "SECRET" in report.removed


def test_drift_detects_changed_value(tmp_lock):
    pin_env(ENV, tmp_lock)
    mutated = {**ENV, "DB_HOST": "remotehost"}
    report = detect_drift(mutated, tmp_lock)
    assert "DB_HOST" in report.changed


def test_drift_report_to_dict_contains_clean(tmp_lock):
    pin_env(ENV, tmp_lock)
    report = detect_drift(ENV, tmp_lock)
    d = report.to_dict()
    assert d["clean"] is True
    assert d["added"] == []
    assert d["removed"] == []
    assert d["changed"] == []


def test_drift_results_are_sorted(tmp_lock):
    pin_env({}, tmp_lock)
    env = {"Z_KEY": "1", "A_KEY": "2", "M_KEY": "3"}
    report = detect_drift(env, tmp_lock)
    assert report.added == sorted(report.added)
