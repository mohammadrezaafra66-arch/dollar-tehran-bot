from app.core.queue import QueueManager
from app.core.audit_logger import AuditLogger
from app.core.speed_profile import SpeedProfileRuntime


class Worker:
    def __init__(self):
        self.queue = QueueManager()
        self.audit = AuditLogger()
        self.speed_runtime = SpeedProfileRuntime()

    def process_next_job(self):
        job = self.queue.get_next_job()

        if not job:
            return None

        self.audit.log(
            action='job_started',
            entity_type='job',
            entity_id=job['id']
        )

        self.speed_runtime.sleep(job.get('speed_profile', 'safe'))

        self.queue.complete_job(job['id'])

        self.audit.log(
            action='job_completed',
            entity_type='job',
            entity_id=job['id']
        )

        return job
