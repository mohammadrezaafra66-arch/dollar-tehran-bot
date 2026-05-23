import time


class WorkerSupervisor:
    def __init__(self, worker_pool, shutdown_manager=None, interval=5):
        self.worker_pool = worker_pool
        self.shutdown_manager = shutdown_manager
        self.interval = interval
        self.running = False

    def run(self):
        self.running = True

        while self.running:
            if self.shutdown_manager and self.shutdown_manager.should_shutdown():
                self.running = False
                break

            self.worker_pool.process()
            time.sleep(self.interval)

    def stop(self):
        self.running = False
