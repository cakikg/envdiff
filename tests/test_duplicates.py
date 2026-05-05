"""Tests for envdiff.duplicates."""
from pathlib import Path

import pytest

from envdiff.duplicates import find_duplicates, DuplicateReport


@pytest.fixture()
def tmp_env(tmp_path):
    def _write(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")
        return p
    return _write


def test_clean_files_return_empty_report(tmp_env):
    a = tmp_env("a.env", "FOO=1\nBAR=2\n")
    b = tmp_env("b.env", "BAZ=3\n")
    report = find_duplicates([a, b])
    assert report.clean


def test_cross_file_duplicate_detected(tmp_env):
    a = tmp_env("a.env", "FOO=1\nBAR=2\n")
    b = tmp_env("b.env", "FOO=99\nBAZ=3\n")
    report = find_duplicates([a, b])
    assert "FOO" in report.cross_file
    assert len(report.cross_file["FOO"]) == 2


def test_cross_file_lists_correct_files(tmp_env):
    a = tmp_env("a.env", "SHARED=1\n")
    b = tmp_env("b.env", "SHARED=2\n")
    report = find_duplicates([a, b])
    paths = report.cross_file["SHARED"]
    assert str(a) in paths
    assert str(b) in paths


def test_within_file_duplicate_detected(tmp_env):
    a = tmp_env("a.env", "FOO=1\nFOO=2\n")
    report = find_duplicates([a])
    assert str(a) in report.within_file
    assert "FOO" in report.within_file[str(a)]


def test_within_file_unique_keys_not_flagged(tmp_env):
    a = tmp_env("a.env", "FOO=1\nBAR=2\n")
    report = find_duplicates([a])
    assert not report.has_within_file


def test_comments_and_blanks_ignored(tmp_env):
    a = tmp_env("a.env", "# comment\n\nFOO=1\n")
    b = tmp_env("b.env", "BAR=2\n")
    report = find_duplicates([a, b])
    assert report.clean


def test_to_dict_structure(tmp_env):
    a = tmp_env("a.env", "FOO=1\nFOO=2\n")
    report = find_duplicates([a])
    d = report.to_dict()
    assert "cross_file" in d
    assert "within_file" in d


def test_multiple_cross_file_keys(tmp_env):
    a = tmp_env("a.env", "A=1\nB=2\n")
    b = tmp_env("b.env", "A=9\nB=8\n")
    report = find_duplicates([a, b])
    assert "A" in report.cross_file
    assert "B" in report.cross_file
