from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class RuntimeFlowContext:
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: dict = field(default_factory=dict)


class RuntimeFlowNode(ABC):
    @abstractmethod
    async def execute(self, payload: dict, context: RuntimeFlowContext):
        pass
