"""Tests for envdiff.differ2 (frequency analyzer)."""
from __future__ import annotations

import pytest
from pathlib import Path

from envdiff.differ2 import analyze_frequency, FrequencyReport


@pytest.fixture()
def tmp_env(tmp_path):
    def _write(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(content)
        return p
    return _write


def test_empty_file_list_gives_empty_report():
    report = analyze_frequency([])
    assert report.total_files == 0
    assert report.counts == {}


def test_single_file_all_keys_have_count_one(tmp_env):
    p = tmp_env("a.env", "FOO=1\nBAR=2\n")
    report = analyze_frequency([p])
    assert report.counts["FOO"] == 1
    assert report.counts["BAR"] == 1


def test_key_present_in_both_files_has_count_two(tmp_env):
    p1 = tmp_env("a.env", "FOO=1\nBAR=2\n")
    p2 = tmp_env("b.env", "FOO=10\nBAZ=3\n")
    report = analyze_frequency([p1, p2])
    assert report.counts["FOO"] == 2
    assert report.counts["BAR"] == 1
    assert report.counts["BAZ"] == 1


def test_coverage_full_for_universal_key(tmp_env):
    p1 = tmp_env("a.env", "FOO=1\n")
    p2 = tmp_env("b.env", "FOO=2\n")
    report = analyze_frequency([p1, p2])
    assert report.coverage("FOO") == 1.0


def test_coverage_partial_for_rare_key(tmp_env):
    p1 = tmp_env("a.env", "FOO=1\nRAREKEY=x\n")
    p2 = tmp_env("b.env", "FOO=2\n")
    report = analyze_frequency([p1, p2])
    assert report.coverage("RAREKEY") == pytest.approx(0.5)


def test_coverage_zero_for_unknown_key(tmp_env):
    p = tmp_env("a.env", "FOO=1\n")
    report = analyze_frequency([p])
    assert report.coverage("GHOST") == 0.0


def test_common_keys_returns_universal_keys(tmp_env):
    p1 = tmp_env("a.env", "FOO=1\nBAR=x\n")
    p2 = tmp_env("b.env", "FOO=2\n")
    report = analyze_frequency([p1, p2])
    assert "FOO" in report.common_keys(threshold=1.0)
    assert "BAR" not in report.common_keys(threshold=1.0)


def test_rare_keys_returns_infrequent_keys(tmp_env):
    p1 = tmp_env("a.env", "FOO=1\nRAREKEY=x\n")
    p2 = tmp_env("b.env", "FOO=2\n")
    report = analyze_frequency([p1, p2])
    rare = report.rare_keys(threshold=1.0)
    assert "RAREKEY" in rare
    assert "FOO" not in rare


def test_to_dict_contains_expected_keys(tmp_env):
    p = tmp_env("a.env", "FOO=1\n")
    report = analyze_frequency([p])
    d = report.to_dict()
    assert "files" in d
    assert "total_files" in d
    assert "counts" in d
    assert "coverage" in d


def test_total_files_matches_input_count(tmp_env):
    p1 = tmp_env("a.env", "FOO=1\n")
    p2 = tmp_env("b.env", "BAR=2\n")
    p3 = tmp_env("c.env", "BAZ=3\n")
    report = analyze_frequency([p1, p2, p3])
    assert report.total_files == 3
