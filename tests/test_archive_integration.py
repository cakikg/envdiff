"""Integration tests: archive round-trip across create → list → extract."""
from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from envdiff.archive_cmd import run_archive_create, run_archive_extract, run_archive_list
from envdiff.archiver import archive_env_files, extract_archive


@pytest.fixture()
def env_files(tmp_path):
    files = {}
    for name, content in [
        (".env.dev", "APP=myapp\nSECRET_KEY=devsecret\nDB_URL=sqlite:///dev.db\n"),
        (".env.prod", "APP=myapp\nSECRET_KEY=prodsecret\nDB_URL=postgres://prod/db\n"),
    ]:
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")
        files[name] = p
    return files


def test_round_trip_preserves_non_sensitive_values(env_files, tmp_path):
    dest = tmp_path / "bundle.zip"
    archive_env_files(list(env_files.values()), dest, redact=True)
    out_dir = tmp_path / "extracted"
    extracted = extract_archive(dest, out_dir)
    names = {p.name for p in extracted}
    assert ".env.dev" in names
    content = (out_dir / ".env.dev").read_text()
    assert "APP=myapp" in content


def test_round_trip_redacts_secrets(env_files, tmp_path):
    dest = tmp_path / "bundle.zip"
    archive_env_files(list(env_files.values()), dest, redact=True)
    out_dir = tmp_path / "extracted"
    extract_archive(dest, out_dir)
    for name in (".env.dev", ".env.prod"):
        content = (out_dir / name).read_text()
        assert "secret" not in content.lower()
        assert "<REDACTED>" in content


def test_cmd_create_then_list_json(env_files, tmp_path):
    dest = tmp_path / "bundle.zip"
    args_create = types.SimpleNamespace(
        files=[str(p) for p in env_files.values()],
        output=str(dest),
        format="json",
        no_redact=False,
    )
    assert run_archive_create(args_create) == 0
    args_list = types.SimpleNamespace(archive=str(dest), format="json")
    # should exit zero
    assert run_archive_list(args_list) == 0


def test_extract_count_matches_input(env_files, tmp_path):
    dest = tmp_path / "bundle.zip"
    archive_env_files(list(env_files.values()), dest)
    out_dir = tmp_path / "out"
    extracted = extract_archive(dest, out_dir)
    # manifest.json is excluded from extraction
    assert len(extracted) == len(env_files)
