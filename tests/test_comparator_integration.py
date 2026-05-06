"""Integration tests: comparator + compare_cmd working end-to-end."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from envdiff.compare_cmd import run_compare
from envdiff.comparator import compare_envs


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


def _args(**kwargs):
    defaults = {"format": "text", "names": None, "show_values": False}
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_three_env_files_all_consistent(tmp_path):
    a = _write(tmp_path, "dev.env", "DB_URL=postgres://dev\nSECRET=abc\n")
    b = _write(tmp_path, "stg.env", "DB_URL=postgres://stg\nSECRET=abc\n")
    c = _write(tmp_path, "prd.env", "DB_URL=postgres://prd\nSECRET=abc\n")
    report = compare_envs([a, b, c], names=["dev", "stg", "prd"])
    # SECRET is consistent; DB_URL differs — inconsistent but not missing
    assert report.missing_keys == []
    assert len(report.inconsistent_keys) == 1
    assert report.inconsistent_keys[0].key == "DB_URL"


def test_json_round_trip_matches_report(tmp_path, capsys):
    a = _write(tmp_path, "a.env", "FOO=1\nBAR=2\n")
    b = _write(tmp_path, "b.env", "FOO=1\n")
    report = compare_envs([a, b])
    run_compare(_args(files=[str(a), str(b)], format="json"))
    data = json.loads(capsys.readouterr().out)
    assert data["all_ok"] == report.all_ok
    assert len(data["keys"]) == len(report.statuses)


def test_custom_names_appear_in_missing_in(tmp_path):
    a = _write(tmp_path, "a.env", "ONLY_IN_A=1\n")
    b = _write(tmp_path, "b.env", "")
    report = compare_envs([a, b], names=["alpha", "beta"])
    key = report.statuses[0]
    assert "beta" in key.missing_in


def test_all_keys_present_in_report(tmp_path):
    a = _write(tmp_path, "a.env", "X=1\nY=2\nZ=3\n")
    b = _write(tmp_path, "b.env", "X=1\nY=2\n")
    report = compare_envs([a, b])
    keys = {s.key for s in report.statuses}
    assert keys == {"X", "Y", "Z"}
