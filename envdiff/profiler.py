"""Profile an .env file: count keys, detect sensitive keys, summarise value types."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from envdiff.core import parse_env_file
from envdiff.redactor import Redactor

_URL_RE = re.compile(r"https?://", re.IGNORECASE)
_INT_RE = re.compile(r"^-?\d+$")
_BOOL_RE = re.compile(r"^(true|false|yes|no|1|0)$", re.IGNORECASE)


@dataclass
class ProfileReport:
    path: str
    total_keys: int
    empty_keys: List[str] = field(default_factory=list)
    sensitive_keys: List[str] = field(default_factory=list)
    url_keys: List[str] = field(default_factory=list)
    int_keys: List[str] = field(default_factory=list)
    bool_keys: List[str] = field(default_factory=list)
    string_keys: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "path": self.path,
            "total_keys": self.total_keys,
            "empty_keys": self.empty_keys,
            "sensitive_keys": self.sensitive_keys,
            "url_keys": self.url_keys,
            "int_keys": self.int_keys,
            "bool_keys": self.bool_keys,
            "string_keys": self.string_keys,
        }


def profile_env_file(path: str | Path, redactor: Redactor | None = None) -> ProfileReport:
    """Parse *path* and return a :class:`ProfileReport`."""
    if redactor is None:
        redactor = Redactor()

    env = parse_env_file(str(path))
    empty: List[str] = []
    sensitive: List[str] = []
    urls: List[str] = []
    ints: List[str] = []
    bools: List[str] = []
    strings: List[str] = []

    for key, value in env.items():
        if value == "":
            empty.append(key)
            continue
        if redactor.is_sensitive(key):
            sensitive.append(key)
        if _URL_RE.search(value):
            urls.append(key)
        elif _INT_RE.match(value):
            ints.append(key)
        elif _BOOL_RE.match(value):
            bools.append(key)
        else:
            strings.append(key)

    return ProfileReport(
        path=str(path),
        total_keys=len(env),
        empty_keys=sorted(empty),
        sensitive_keys=sorted(sensitive),
        url_keys=sorted(urls),
        int_keys=sorted(ints),
        bool_keys=sorted(bools),
        string_keys=sorted(strings),
    )
