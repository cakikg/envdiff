"""Tests for envdiff.auditor."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.auditor import (
    AuditEntry,
    clear_audit_log,
    list_entries,
    load_entry,
    record,
)


@pytest.fixture()
def audit_dir(tmp_path: Path) -> Path:
    return tmp_path / "audit"


def test_record_creates_file(audit_dir: Path) -> None:
    entry = AuditEntry(operation="diff", files=[".env", ".env.prod"])
    path = record(entry, audit_dir=audit_dir)
    assert path.exists()


def test_record_round_trips(audit_dir: Path) -> None:
    entry = AuditEntry(operation="merge", files=[".env"], details={"strategy": "first"})
    path = record(entry, audit_dir=audit_dir)
    loaded = load_entry(path)
    assert loaded.operation == "merge"
    assert loaded.files == [".env"]
    assert loaded.details["strategy"] == "first"


def test_list_entries_empty(audit_dir: Path) -> None:
    assert list_entries(audit_dir) == []


def test_list_entries_returns_all(audit_dir: Path) -> None:
    for op in ("diff", "lint", "validate"):
        record(AuditEntry(operation=op, files=[]), audit_dir=audit_dir)
    entries = list_entries(audit_dir)
    assert len(entries) == 3
    ops = {e.operation for e in entries}
    assert ops == {"diff", "lint", "validate"}


def test_list_entries_skips_corrupt_file(audit_dir: Path) -> None:
    audit_dir.mkdir(parents=True, exist_ok=True)
    (audit_dir / "bad_entry.json").write_text("not json{{{")
    record(AuditEntry(operation="diff", files=[]), audit_dir=audit_dir)
    entries = list_entries(audit_dir)
    assert len(entries) == 1


def test_clear_audit_log_removes_files(audit_dir: Path) -> None:
    for i in range(3):
        record(AuditEntry(operation=f"op{i}", files=[]), audit_dir=audit_dir)
    removed = clear_audit_log(audit_dir)
    assert removed == 3
    assert list_entries(audit_dir) == []


def test_clear_audit_log_nonexistent_dir(audit_dir: Path) -> None:
    assert clear_audit_log(audit_dir) == 0


def test_entry_to_dict_has_required_keys() -> None:
    entry = AuditEntry(operation="sort", files=[".env"])
    d = entry.to_dict()
    assert "operation" in d
    assert "files" in d
    assert "timestamp" in d
    assert "user" in d


def test_entry_from_dict_round_trip() -> None:
    original = AuditEntry(operation="rename", files=[".env"], details={"old": "FOO", "new": "BAR"})
    restored = AuditEntry.from_dict(original.to_dict())
    assert restored.operation == original.operation
    assert restored.details == original.details
