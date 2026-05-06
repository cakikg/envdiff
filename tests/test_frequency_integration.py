"""Integration tests: frequency analyzer + cmd together."""
from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from envdiff.differ2 import analyze_frequency
from envdiff.frequency_cmd import run_frequency


@pytest.fixture()
def env_files(tmp_path):
    files = {
        "prod": "DB_HOST=prod-db\nDB_PORT=5432\nSECRET_KEY=abc\nDEBUG=false\n",
        "staging": "DB_HOST=staging-db\nDB_PORT=5432\nSECRET_KEY=xyz\nDEBUG=true\n",
        "dev": "DB_HOST=localhost\nDB_PORT=5432\nDEBUG=true\nEXTRA_DEV=1\n",
    }
    paths = {}
    for name, content in files.items():
        p = tmp_path / f"{name}.env"
        p.write_text(content)
        paths[name] = p
    return paths


def test_universal_keys_have_full_coverage(env_files):
    report = analyze_frequency(list(env_files.values()))
    assert report.coverage("DB_HOST") == pytest.approx(1.0)
    assert report.coverage("DB_PORT") == pytest.approx(1.0)
    assert report.coverage("DEBUG") == pytest.approx(1.0)


def test_rare_key_detected(env_files):
    report = analyze_frequency(list(env_files.values()))
    assert report.coverage("EXTRA_DEV") == pytest.approx(1 / 3)
    assert "EXTRA_DEV" in report.rare_keys(threshold=1.0)


def test_secret_key_missing_from_dev(env_files):
    report = analyze_frequency(list(env_files.values()))
    assert report.counts.get("SECRET_KEY", 0) == 2
    assert report.coverage("SECRET_KEY") == pytest.approx(2 / 3)


def test_json_output_matches_direct_report(env_files, capsys):
    paths = list(env_files.values())
    report = analyze_frequency(paths)
    args = Namespace(
        files=[str(p) for p in paths],
        format="json",
        threshold=1.0,
        show_rare=False,
    )
    run_frequency(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["total_files"] == report.total_files
    assert data["counts"] == report.counts
