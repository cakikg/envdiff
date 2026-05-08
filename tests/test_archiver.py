"""Unit tests for envdiff.archiver."""
from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from envdiff.archiver import ArchiveResult, archive_env_files, extract_archive, list_archive


@pytest.fixture()
def tmp_env(tmp_path):
    def _write(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")
        return p

    return _write


def test_archive_creates_zip(tmp_env, tmp_path):
    f1 = tmp_env(".env.dev", "APP_NAME=dev\nSECRET_KEY=abc123\n")
    dest = tmp_path / "bundle.zip"
    result = archive_env_files([f1], dest)
    assert dest.exists()
    assert zipfile.is_zipfile(dest)


def test_archive_result_lists_files(tmp_env, tmp_path):
    f1 = tmp_env(".env.dev", "APP_NAME=dev\n")
    f2 = tmp_env(".env.prod", "APP_NAME=prod\n")
    dest = tmp_path / "bundle.zip"
    result = archive_env_files([f1, f2], dest)
    assert ".env.dev" in result.files_added
    assert ".env.prod" in result.files_added
    assert len(result.files_added) == 2


def test_archive_redacts_sensitive_keys(tmp_env, tmp_path):
    f1 = tmp_env(".env", "SECRET_KEY=mysecret\nAPP_NAME=hello\n")
    dest = tmp_path / "bundle.zip"
    archive_env_files([f1], dest, redact=True)
    with zipfile.ZipFile(dest, "r") as zf:
        content = zf.read(".env").decode()
    assert "mysecret" not in content
    assert "<REDACTED>" in content
    assert "APP_NAME=hello" in content


def test_archive_no_redact_keeps_values(tmp_env, tmp_path):
    f1 = tmp_env(".env", "SECRET_KEY=mysecret\n")
    dest = tmp_path / "bundle.zip"
    archive_env_files([f1], dest, redact=False)
    with zipfile.ZipFile(dest, "r") as zf:
        content = zf.read(".env").decode()
    assert "mysecret" in content


def test_archive_includes_manifest(tmp_env, tmp_path):
    f1 = tmp_env(".env", "KEY=val\n")
    dest = tmp_path / "bundle.zip"
    archive_env_files([f1], dest)
    names = list_archive(dest)
    assert "manifest.json" in names


def test_archive_missing_file_raises(tmp_path):
    dest = tmp_path / "bundle.zip"
    with pytest.raises(FileNotFoundError):
        archive_env_files([Path("/nonexistent/.env")], dest)


def test_list_archive_returns_names(tmp_env, tmp_path):
    f1 = tmp_env(".env.staging", "X=1\n")
    dest = tmp_path / "bundle.zip"
    archive_env_files([f1], dest)
    names = list_archive(dest)
    assert ".env.staging" in names


def test_extract_archive_restores_files(tmp_env, tmp_path):
    f1 = tmp_env(".env.dev", "APP=dev\nDB=sqlite\n")
    dest = tmp_path / "bundle.zip"
    archive_env_files([f1], dest, redact=False)
    out_dir = tmp_path / "extracted"
    files = extract_archive(dest, out_dir)
    assert len(files) == 1
    assert (out_dir / ".env.dev").exists()
    assert "APP=dev" in (out_dir / ".env.dev").read_text()


def test_result_to_dict_keys(tmp_env, tmp_path):
    f1 = tmp_env(".env", "A=1\n")
    dest = tmp_path / "bundle.zip"
    result = archive_env_files([f1], dest)
    d = result.to_dict()
    assert "archive_path" in d
    assert "files_added" in d
    assert "size_bytes" in d
    assert d["size_bytes"] > 0
