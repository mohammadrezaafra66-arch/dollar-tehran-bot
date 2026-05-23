from dataclasses import dataclass, asdict
from datetime import datetime
import uuid


@dataclass
class TraceContext:
    trace_id: str
    job_id: str = ''
    worker_id: str = ''
    instance_id: str = ''
    plugin_name: str = ''
    stage_name: str = ''
    created_at: str = datetime.utcnow().isoformat()

    @classmethod
    def create(cls, **kwargs):
        return cls(trace_id=str(uuid.uuid4()), **kwargs)

    def child(self, **kwargs):
        data = asdict(self)
        data.update(kwargs)
        return TraceContext(**data)

    def to_log_context(self):
        return asdict(self)
