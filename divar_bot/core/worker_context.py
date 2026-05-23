from dataclasses import dataclass


@dataclass
class WorkerContext:
    worker_id: str
    instance_id: str
    speed_profile: str = 'safe'
    shutdown_requested: bool = False
