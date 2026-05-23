import signal


class ShutdownManager:
    def __init__(self):
        self.shutdown_requested = False
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame):
        self.shutdown_requested = True

    def should_shutdown(self):
        return self.shutdown_requested
