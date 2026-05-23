import json

from app.core.queue import QueueManager
from app.core.audit_logger import AuditLogger
from app.core.speed_profile import SpeedProfileRuntime
from app.plugins.divar.plugin import DivarPlugin
from app.plugins.divar.parser import DivarParser
from app.repositories.extraction_repository import ExtractionRepository


class Worker:
    def __init__(self):
        self.queue = QueueManager()
        self.audit = AuditLogger()
        self.speed_runtime = SpeedProfileRuntime()
        self.extraction_repository = ExtractionRepository()
        self.plugins = {
            'divar': DivarPlugin()
        }

    def process_next_job(self):
        job = self.queue.get_next_job()

        if not job:
            return None

        self.audit.log(
            action='job_started',
            entity_type='job',
            entity_id=job['id']
        )

        try:
            payload = json.loads(job['payload'])
            plugin = self.plugins.get(job['plugin_name'])

            if not plugin:
                raise RuntimeError(f"Plugin not found: {job['plugin_name']}")

            if job['plugin_name'] == 'divar':
                url = payload.get('url')
                plugin.start()
                raw_result = plugin.extract(url)
                plugin.stop()

                parser = DivarParser()
                normalized = parser.normalize(raw_result)
                self.extraction_repository.save('divar', normalized)

            self.speed_runtime.sleep(job.get('speed_profile', 'safe'))
            self.queue.complete_job(job['id'])

            self.audit.log(
                action='job_completed',
                entity_type='job',
                entity_id=job['id']
            )

        except Exception as exc:
            self.queue.fail_job(job['id'], str(exc))
            self.audit.log(
                action='job_failed',
                entity_type='job',
                entity_id=job['id'],
                details=str(exc)
            )
            raise

        return job
