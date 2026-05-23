from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


@dataclass
class RuntimeStatus:
    instance_id: str
    status: str = 'starting'
    active_workers: int = 0
    queue_depth: int = 0
    last_job_id: Optional[str] = None
    last_error: Optional[str] = None
    started_at: str = datetime.utcnow().isoformat()
    updated_at: str = datetime.utcnow().isoformat()

    def mark_running(self):
        self.status = 'running'
        self.updated_at = datetime.utcnow().isoformat()

    def mark_degraded(self, error):
        self.status = 'degraded'
        self.last_error = str(error)
        self.updated_at = datetime.utcnow().isoformat()

    def mark_stopping(self):
        self.status = 'stopping'
        self.updated_at = datetime.utcnow().isoformat()

    def snapshot(self):
        return asdict(self)
