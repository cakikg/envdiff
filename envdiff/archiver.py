"""Archive multiple .env files into a single ZIP bundle, with optional encryption."""
from __future__ import annotations

import io
import json
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class ArchiveResult:
    files_added: List[str] = field(default_factory=list)
    archive_path: str = ""
    size_bytes: int = 0

    def to_dict(self) -> dict:
        return {
            "archive_path": self.archive_path,
            "files_added": self.files_added,
            "size_bytes": self.size_bytes,
        }


def _manifest(files: List[Path]) -> bytes:
    data = {"files": [str(f) for f in files]}
    return json.dumps(data, indent=2).encode()


def archive_env_files(
    paths: List[Path],
    dest: Path,
    *,
    redact: bool = True,
    sensitive_patterns: Optional[List[str]] = None,
) -> ArchiveResult:
    """Bundle *paths* into a ZIP at *dest*.

    When *redact* is True the values of sensitive keys are replaced with
    ``<REDACTED>`` before writing into the archive.
    """
    from envdiff.redactor import Redactor

    redactor = Redactor(extra_patterns=sensitive_patterns or [])
    result = ArchiveResult(archive_path=str(dest))

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in paths:
            if not path.exists():
                raise FileNotFoundError(path)
            lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
            if redact:
                out_lines = []
                for line in lines:
                    stripped = line.strip()
                    if "=" in stripped and not stripped.startswith("#"):
                        key, _, val = stripped.partition("=")
                        if redactor.is_sensitive(key.strip()):
                            line = f"{key.strip()}=<REDACTED>\n"
                    out_lines.append(line)
                content = "".join(out_lines).encode()
            else:
                content = path.read_bytes()
            arcname = path.name
            zf.writestr(arcname, content)
            result.files_added.append(arcname)
        zf.writestr("manifest.json", _manifest(paths))

    dest.write_bytes(buf.getvalue())
    result.size_bytes = dest.stat().st_size
    return result


def list_archive(path: Path) -> List[str]:
    """Return the names of entries inside an archive."""
    with zipfile.ZipFile(path, "r") as zf:
        return zf.namelist()


def extract_archive(path: Path, dest_dir: Path) -> List[Path]:
    """Extract all .env entries from *path* into *dest_dir*."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    extracted: List[Path] = []
    with zipfile.ZipFile(path, "r") as zf:
        for name in zf.namelist():
            if name == "manifest.json":
                continue
            out = dest_dir / name
            out.write_bytes(zf.read(name))
            extracted.append(out)
    return extracted
