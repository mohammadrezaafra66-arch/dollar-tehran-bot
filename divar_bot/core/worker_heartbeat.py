from datetime import datetime


class WorkerHeartbeatRegistry:
    def __init__(self):
        self.registry = {}

    def beat(self, worker_id, instance_id, current_job_id=None):
        self.registry[worker_id] = {
            'instance_id': instance_id,
            'current_job_id': current_job_id,
            'last_heartbeat_at': datetime.utcnow().isoformat(),
            'status': 'alive',
        }

    def mark_dead(self, worker_id):
        if worker_id in self.registry:
            self.registry[worker_id]['status'] = 'dead'

    def snapshot(self):
        return self.registry
