"""Snapshot: save and restore .env file states for later diffing."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_SNAPSHOT_DIR = Path(".envdiff_snapshots")


def _snapshot_path(name: str, snapshot_dir: Path) -> Path:
    return snapshot_dir / f"{name}.json"


def save_snapshot(
    env_data: Dict[str, str],
    name: str,
    snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR,
    label: Optional[str] = None,
) -> Path:
    """Persist *env_data* as a named snapshot.  Returns the written path."""
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "name": name,
        "label": label or name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "env": env_data,
    }
    dest = _snapshot_path(name, snapshot_dir)
    dest.write_text(json.dumps(payload, indent=2))
    return dest


def load_snapshot(
    name: str,
    snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR,
) -> Dict[str, object]:
    """Load a previously saved snapshot.  Raises FileNotFoundError if absent."""
    path = _snapshot_path(name, snapshot_dir)
    if not path.exists():
        raise FileNotFoundError(f"Snapshot '{name}' not found in {snapshot_dir}")
    return json.loads(path.read_text())


def list_snapshots(snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR) -> List[Dict[str, str]]:
    """Return metadata (name, label, created_at) for all saved snapshots."""
    if not snapshot_dir.exists():
        return []
    results = []
    for p in sorted(snapshot_dir.glob("*.json")):
        try:
            data = json.loads(p.read_text())
            results.append({
                "name": data.get("name", p.stem),
                "label": data.get("label", ""),
                "created_at": data.get("created_at", ""),
            })
        except (json.JSONDecodeError, OSError):
            continue
    return results


def delete_snapshot(
    name: str,
    snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR,
) -> bool:
    """Delete a snapshot by name.  Returns True if deleted, False if not found."""
    path = _snapshot_path(name, snapshot_dir)
    if path.exists():
        path.unlink()
        return True
    return False
