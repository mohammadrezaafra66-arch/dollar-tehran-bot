from app.core.worker import Worker


class WorkerPool:
    def __init__(self, size=1):
        self.size = size
        self.workers = [Worker() for _ in range(size)]

    def process(self):
        results = []

        for worker in self.workers:
            result = worker.process_next_job()
            results.append(result)

        return results
