from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class CredentialProviderPort(ABC):
    @abstractmethod
    async def resolve(self, identity_id: str) -> dict[str, Any]:
        """Resolve credential payload for a runtime identity."""

    @abstractmethod
    async def rotate(self, identity_id: str) -> None:
        """Rotate credential material for a runtime identity."""

    @abstractmethod
    async def health(self) -> dict[str, Any]:
        """Return provider health information."""
