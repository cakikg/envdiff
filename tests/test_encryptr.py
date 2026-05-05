"""Tests for envdiff.encryptr."""
from __future__ import annotations

import pytest

pytest.importorskip("cryptography", reason="cryptography package not installed")

from envdiff.encryptr import (
    DecryptResult,
    EncryptResult,
    decrypt_values,
    encrypt_env_file,
    generate_key,
)


@pytest.fixture()
def tmp_env(tmp_path):
    return tmp_path / ".env"


def _write(path, content: str) -> None:
    path.write_text(content)


# ---------------------------------------------------------------------------
# generate_key
# ---------------------------------------------------------------------------

def test_generate_key_returns_string():
    key = generate_key()
    assert isinstance(key, str)
    assert len(key) > 0


def test_generate_key_unique():
    assert generate_key() != generate_key()


# ---------------------------------------------------------------------------
# encrypt_env_file
# ---------------------------------------------------------------------------

def test_encrypt_all_keys(tmp_env):
    _write(tmp_env, "SECRET=mysecret\nDB_PASS=hunter2\n")
    key = generate_key()
    result = encrypt_env_file(str(tmp_env), key)
    assert result.ok
    assert "SECRET" in result.encrypted
    assert "DB_PASS" in result.encrypted
    assert result.encrypted["SECRET"] != "mysecret"


def test_encrypt_selected_keys(tmp_env):
    _write(tmp_env, "SECRET=mysecret\nPUBLIC=hello\n")
    key = generate_key()
    result = encrypt_env_file(str(tmp_env), key, keys_to_encrypt=["SECRET"])
    assert result.ok
    assert "SECRET" in result.encrypted
    assert "PUBLIC" in result.skipped
    assert "PUBLIC" not in result.encrypted


def test_encrypt_missing_file_returns_error(tmp_path):
    key = generate_key()
    result = encrypt_env_file(str(tmp_path / "missing.env"), key)
    assert not result.ok
    assert any("not found" in e for e in result.errors)


def test_encrypt_invalid_key_returns_error(tmp_env):
    _write(tmp_env, "A=1\n")
    result = encrypt_env_file(str(tmp_env), "not-a-valid-fernet-key")
    assert not result.ok
    assert any("Invalid key" in e for e in result.errors)


# ---------------------------------------------------------------------------
# decrypt_values
# ---------------------------------------------------------------------------

def test_round_trip_encrypt_decrypt(tmp_env):
    _write(tmp_env, "SECRET=topsecret\nTOKEN=abc123\n")
    key = generate_key()
    enc = encrypt_env_file(str(tmp_env), key)
    assert enc.ok
    dec = decrypt_values(enc.encrypted, key)
    assert dec.ok
    assert dec.decrypted["SECRET"] == "topsecret"
    assert dec.decrypted["TOKEN"] == "abc123"


def test_decrypt_wrong_key_returns_error(tmp_env):
    _write(tmp_env, "SECRET=value\n")
    key1 = generate_key()
    key2 = generate_key()
    enc = encrypt_env_file(str(tmp_env), key1)
    dec = decrypt_values(enc.encrypted, key2)
    assert not dec.ok
    assert any("SECRET" in e for e in dec.errors)


def test_decrypt_invalid_key_returns_error():
    result = decrypt_values({"K": "sometoken"}, "bad-key")
    assert not result.ok
    assert any("Invalid key" in e for e in result.errors)


def test_decrypt_empty_dict_ok():
    key = generate_key()
    result = decrypt_values({}, key)
    assert result.ok
    assert result.decrypted == {}
