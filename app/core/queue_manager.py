from __future__ import annotations

from queue import Queue
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class QueueJob:
    platform: str
    query: str
    priority: int = 1
    status: str = 'pending'
    retry_count: int = 0
    last_error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class QueueManager:
    def __init__(self):
        self.queue: Queue = Queue()

    def add_job(self, job: QueueJob):
        self.queue.put(job)

    def get_job(self) -> Optional[QueueJob]:
        if self.queue.empty():
            return None
        return self.queue.get()

    def size(self) -> int:
        return self.queue.qsize()
