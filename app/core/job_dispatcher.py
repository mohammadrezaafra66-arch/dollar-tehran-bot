from app.core.plugin_manager import PluginManager


class JobDispatcher:
    def __init__(self):
        self.plugin_manager = PluginManager()

    def dispatch(self, job):
        plugin = self.plugin_manager.plugins.get(job['plugin_name'])

        if not plugin:
            raise RuntimeError('Plugin not registered')

        return plugin
