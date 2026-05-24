from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import uuid


@dataclass
class AIRequest:
    payload: dict[str, Any]
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    version: str = "v1"


@dataclass
class AIResponse:
    payload: dict[str, Any]
    provider: str
    model: str
    trace_id: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class AIServicePort(ABC):
    @abstractmethod
    async def execute(
        self,
        request: AIRequest,
    ) -> AIResponse:
        pass

    @abstractmethod
    async def health(self) -> dict[str, Any]:
        pass
