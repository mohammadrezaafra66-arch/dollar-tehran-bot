import importlib
import pkgutil
from datetime import datetime


class PluginDiscovery:
    def __init__(self):
        self._plugins = {}

    def discover(self, package_name: str):
        package = importlib.import_module(package_name)

        for module in pkgutil.iter_modules(
            package.__path__
        ):
            self._plugins[module.name] = {
                "package": package_name,
                "discovered_at": (
                    datetime.utcnow().isoformat()
                ),
                "status": "discovered",
            }

        return dict(self._plugins)
