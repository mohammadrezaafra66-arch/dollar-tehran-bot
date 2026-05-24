from __future__ import annotations

import base64
import json
import time
from hashlib import sha256
from typing import Any


class EncryptedCredentialCache:
    def __init__(
        self,
        encryption_key: str,
    ):
        self._store: dict[str, dict[str, Any]] = {}
        self._key = sha256(encryption_key.encode()).digest()

    def _xor(self, payload: bytes) -> bytes:
        return bytes(
            byte ^ self._key[index % len(self._key)]
            for index, byte in enumerate(payload)
        )

    def _encrypt(self, data: dict[str, Any]) -> str:
        raw = json.dumps(data).encode()
        encrypted = self._xor(raw)
        return base64.b64encode(encrypted).decode()

    def _decrypt(self, encrypted: str) -> dict[str, Any]:
        payload = base64.b64decode(encrypted.encode())
        decrypted = self._xor(payload)
        return json.loads(decrypted.decode())

    async def get(self, key: str) -> dict[str, Any] | None:
        item = self._store.get(key)

        if not item:
            return None

        if item["expires_at"] < time.time():
            self._store.pop(key, None)
            return None

        return self._decrypt(item["payload"])

    async def get_stale(self, key: str) -> dict[str, Any] | None:
        item = self._store.get(key)

        if not item:
            return None

        return self._decrypt(item["payload"])

    async def set(
        self,
        key: str,
        value: dict[str, Any],
        ttl: int,
    ) -> None:
        self._store[key] = {
            "payload": self._encrypt(value),
            "expires_at": time.time() + ttl,
        }
