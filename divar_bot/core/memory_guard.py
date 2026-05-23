import os


class MemoryGuard:
    def __init__(self, minimum_available_mb=256):
        self.minimum_available_mb = minimum_available_mb

    def is_memory_safe(self):
        try:
            import psutil
        except ImportError:
            return True

        available_memory = psutil.virtual_memory().available / (1024 * 1024)
        return available_memory >= self.minimum_available_mb

    def snapshot(self):
        try:
            import psutil
        except ImportError:
            return {
                'status': 'psutil_not_installed'
            }

        memory = psutil.virtual_memory()

        return {
            'available_mb': round(memory.available / (1024 * 1024), 2),
            'used_percent': memory.percent,
            'pid': os.getpid(),
        }
