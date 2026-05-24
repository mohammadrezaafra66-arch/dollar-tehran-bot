class StaleJobRecovery:
    def __init__(self, lease_manager, logger=None):
        self.lease_manager = lease_manager
        self.logger = logger

    def recoverable_jobs(self, jobs):
        recoverable = []

        for job in jobs:
            lease_until = job.get('locked_until')

            if self.lease_manager.is_expired(lease_until):
                recoverable.append(job)

                if self.logger:
                    self.logger.warning(
                        'stale_job_detected',
                        job_id=job.get('id'),
                        plugin=job.get('plugin_name'),
                    )

        return recoverable
