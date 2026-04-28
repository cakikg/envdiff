"""Unit tests for envdiff.snapshotter."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.snapshotter import (
    delete_snapshot,
    list_snapshots,
    load_snapshot,
    save_snapshot,
)


@pytest.fixture()
def snap_dir(tmp_path: Path) -> Path:
    return tmp_path / "snaps"


def test_save_creates_file(snap_dir: Path) -> None:
    save_snapshot({"KEY": "val"}, "test", snapshot_dir=snap_dir)
    assert (snap_dir / "test.json").exists()


def test_save_round_trips_env(snap_dir: Path) -> None:
    env = {"A": "1", "B": "hello"}
    save_snapshot(env, "rt", snapshot_dir=snap_dir)
    snap = load_snapshot("rt", snapshot_dir=snap_dir)
    assert snap["env"] == env


def test_save_stores_label(snap_dir: Path) -> None:
    save_snapshot({}, "lbl", snapshot_dir=snap_dir, label="My Label")
    snap = load_snapshot("lbl", snapshot_dir=snap_dir)
    assert snap["label"] == "My Label"


def test_save_default_label_is_name(snap_dir: Path) -> None:
    save_snapshot({}, "nolab", snapshot_dir=snap_dir)
    snap = load_snapshot("nolab", snapshot_dir=snap_dir)
    assert snap["label"] == "nolab"


def test_load_missing_raises(snap_dir: Path) -> None:
    with pytest.raises(FileNotFoundError, match="ghost"):
        load_snapshot("ghost", snapshot_dir=snap_dir)


def test_list_empty_dir_returns_empty(snap_dir: Path) -> None:
    assert list_snapshots(snap_dir) == []


def test_list_nonexistent_dir_returns_empty(tmp_path: Path) -> None:
    assert list_snapshots(tmp_path / "nope") == []


def test_list_returns_metadata(snap_dir: Path) -> None:
    save_snapshot({}, "alpha", snapshot_dir=snap_dir, label="Alpha")
    save_snapshot({}, "beta", snapshot_dir=snap_dir, label="Beta")
    names = [s["name"] for s in list_snapshots(snap_dir)]
    assert "alpha" in names and "beta" in names


def test_delete_existing(snap_dir: Path) -> None:
    save_snapshot({}, "del_me", snapshot_dir=snap_dir)
    assert delete_snapshot("del_me", snapshot_dir=snap_dir) is True
    assert not (snap_dir / "del_me.json").exists()


def test_delete_missing_returns_false(snap_dir: Path) -> None:
    assert delete_snapshot("ghost", snapshot_dir=snap_dir) is False


def test_save_returns_path(snap_dir: Path) -> None:
    p = save_snapshot({}, "ret", snapshot_dir=snap_dir)
    assert isinstance(p, Path)
    assert p.suffix == ".json"
