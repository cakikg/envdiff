"""Tests for envdiff.scorer and envdiff.score_cmd."""
from __future__ import annotations

import json
import os
from argparse import Namespace
from pathlib import Path

import pytest

from envdiff.scorer import score_env_file, ScoreReport
from envdiff.score_cmd import run_score, _render_text, _render_json


@pytest.fixture()
def tmp_env(tmp_path: Path):
    def _write(name: str, content: str) -> str:
        p = tmp_path / name
        p.write_text(content)
        return str(p)
    return _write


def test_clean_file_scores_high(tmp_env):
    path = tmp_env("clean.env", "APP_NAME=myapp\nDEBUG=false\nPORT=8080\n")
    report = score_env_file(path)
    assert report.score >= 80


def test_score_report_has_correct_file(tmp_env):
    path = tmp_env("a.env", "KEY=value\n")
    report = score_env_file(path)
    assert report.file == path


def test_grade_a_for_perfect_score():
    r = ScoreReport(file="x", score=100)
    assert r.grade == "A"


def test_grade_f_for_low_score():
    r = ScoreReport(file="x", score=30)
    assert r.grade == "F"


def test_grade_b_for_mid_score():
    r = ScoreReport(file="x", score=80)
    assert r.grade == "B"


def test_empty_keys_reduce_score(tmp_env):
    path = tmp_env("empty.env", "KEY=\nOTHER=\nANOTHER=\n")
    report = score_env_file(path)
    assert report.score < 100
    assert any("empty" in p for p in report.penalties)


def test_duplicate_key_reduces_score(tmp_env):
    path = tmp_env("dup.env", "KEY=a\nKEY=b\n")
    report = score_env_file(path)
    assert report.score < 100


def test_score_never_below_zero(tmp_env):
    content = "KEY=\n" * 30 + "KEY=dup\n" * 10
    path = tmp_env("bad.env", content)
    report = score_env_file(path)
    assert report.score >= 0


def test_to_dict_contains_grade(tmp_env):
    path = tmp_env("d.env", "X=1\n")
    d = score_env_file(path).to_dict()
    assert "grade" in d
    assert "score" in d
    assert "penalties" in d


def test_run_score_exits_zero_for_good_file(tmp_env):
    path = tmp_env("ok.env", "APP=hello\n")
    args = Namespace(files=[path], format="text", min_score=0)
    assert run_score(args) == 0


def test_run_score_exits_one_for_missing_file(tmp_env):
    args = Namespace(files=["/nonexistent/file.env"], format="text", min_score=0)
    assert run_score(args) == 1


def test_run_score_json_output(tmp_env, capsys):
    path = tmp_env("j.env", "KEY=val\n")
    args = Namespace(files=[path], format="json", min_score=0)
    run_score(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert data[0]["file"] == path


def test_run_score_min_score_threshold(tmp_env):
    path = tmp_env("thresh.env", "KEY=\n" * 10)
    args = Namespace(files=[path], format="text", min_score=95)
    assert run_score(args) == 1
