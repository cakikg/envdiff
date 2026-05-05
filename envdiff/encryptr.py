"""Encrypt and decrypt .env file values using Fernet symmetric encryption."""
from __future__ import annotations

import base64
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:  # pragma: no cover
    Fernet = None  # type: ignore
    InvalidToken = Exception  # type: ignore

from envdiff.core import parse_env_file


@dataclass
class EncryptResult:
    encrypted: Dict[str, str] = field(default_factory=dict)
    skipped: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict:
        return {
            "encrypted": self.encrypted,
            "skipped": self.skipped,
            "errors": self.errors,
        }


@dataclass
class DecryptResult:
    decrypted: Dict[str, str] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict:
        return {"decrypted": self.decrypted, "errors": self.errors}


def generate_key() -> str:
    """Generate a new Fernet key and return it as a URL-safe base64 string."""
    if Fernet is None:
        raise RuntimeError("cryptography package is required: pip install cryptography")
    return Fernet.generate_key().decode()


def encrypt_env_file(
    path: str,
    key: str,
    keys_to_encrypt: Optional[List[str]] = None,
) -> EncryptResult:
    """Encrypt values in *path* for the given *keys_to_encrypt* (all keys if None)."""
    if Fernet is None:
        raise RuntimeError("cryptography package is required: pip install cryptography")

    result = EncryptResult()
    try:
        fernet = Fernet(key.encode() if isinstance(key, str) else key)
    except Exception as exc:
        result.errors.append(f"Invalid key: {exc}")
        return result

    try:
        env = parse_env_file(path)
    except FileNotFoundError:
        result.errors.append(f"File not found: {path}")
        return result

    for k, v in env.items():
        if keys_to_encrypt is not None and k not in keys_to_encrypt:
            result.skipped.append(k)
            continue
        token = fernet.encrypt(v.encode()).decode()
        result.encrypted[k] = token

    return result


def decrypt_values(
    encrypted: Dict[str, str],
    key: str,
) -> DecryptResult:
    """Decrypt a dict of Fernet-encrypted values."""
    if Fernet is None:
        raise RuntimeError("cryptography package is required: pip install cryptography")

    result = DecryptResult()
    try:
        fernet = Fernet(key.encode() if isinstance(key, str) else key)
    except Exception as exc:
        result.errors.append(f"Invalid key: {exc}")
        return result

    for k, v in encrypted.items():
        try:
            result.decrypted[k] = fernet.decrypt(v.encode()).decode()
        except InvalidToken:
            result.errors.append(f"Failed to decrypt key '{k}': invalid token or wrong key")

    return result
