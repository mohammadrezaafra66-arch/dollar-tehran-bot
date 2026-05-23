class QueueManager:
    def __init__(self):
        self.jobs = []

    def add_job(self, job):
        self.jobs.append(job)

    def get_next_job(self):
        if not self.jobs:
            return None

        return self.jobs.pop(0)
