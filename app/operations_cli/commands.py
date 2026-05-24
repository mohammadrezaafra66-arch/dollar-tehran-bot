from datetime import datetime


class OperationsCommandRegistry:
    def __init__(self):
        self._commands = {}

    def register(
        self,
        command_name: str,
        metadata=None,
    ):
        metadata = metadata or {}

        self._commands[command_name] = {
            "metadata": metadata,
            "registered_at": datetime.utcnow().isoformat(),
            "status": "active",
        }

    def mark_degraded(self, command_name: str):
        command = self._commands.get(command_name)

        if not command:
            return

        command["status"] = "degraded"

    def snapshot(self):
        return dict(self._commands)
