"""AES-256-GCM envelope for API JSON bodies (v1)."""

from __future__ import annotations

import base64
import json
import os
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

VERSION_PREFIX = "v1."


class PayloadEncryptionError(Exception):
    pass


def _decode_key(key_b64: str) -> bytes:
    if not key_b64:
        raise PayloadEncryptionError("API_PAYLOAD_ENCRYPTION_KEY is not set")
    try:
        key = base64.urlsafe_b64decode(key_b64 + "=" * (-len(key_b64) % 4))
    except Exception as exc:
        raise PayloadEncryptionError("Invalid API_PAYLOAD_ENCRYPTION_KEY encoding") from exc
    if len(key) != 32:
        raise PayloadEncryptionError("API_PAYLOAD_ENCRYPTION_KEY must decode to 32 bytes")
    return key


def encrypt_json(payload: dict[str, Any], *, key_b64: str) -> str:
    key = _decode_key(key_b64)
    plaintext = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    nonce = os.urandom(12)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, None)
    token = base64.urlsafe_b64encode(nonce + ciphertext).decode("ascii").rstrip("=")
    return f"{VERSION_PREFIX}{token}"


def decrypt_json(token: str, *, key_b64: str) -> dict[str, Any]:
    if not token.startswith(VERSION_PREFIX):
        raise PayloadEncryptionError("Unknown encryption version")
    key = _decode_key(key_b64)
    raw = base64.urlsafe_b64decode(token[len(VERSION_PREFIX) :] + "=" * (-len(token[len(VERSION_PREFIX) :]) % 4))
    if len(raw) < 13:
        raise PayloadEncryptionError("Ciphertext too short")
    nonce, ciphertext = raw[:12], raw[12:]
    plaintext = AESGCM(key).decrypt(nonce, ciphertext, None)
    data = json.loads(plaintext.decode("utf-8"))
    if not isinstance(data, dict):
        raise PayloadEncryptionError("Decrypted payload is not a JSON object")
    return data


def is_encrypted_envelope(body: dict[str, Any]) -> bool:
    return body.get("encrypted") is True and isinstance(body.get("payload"), str)


def wrap_encrypted(inner: dict[str, Any], *, key_b64: str) -> dict[str, Any]:
    return {
        "encrypted": True,
        "payload": encrypt_json(inner, key_b64=key_b64),
    }


def unwrap_encrypted(outer: dict[str, Any], *, key_b64: str) -> dict[str, Any]:
    if not is_encrypted_envelope(outer):
        return outer
    return decrypt_json(outer["payload"], key_b64=key_b64)
