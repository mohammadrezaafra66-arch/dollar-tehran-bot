from app.core.plugin_manager import PluginManager


class PluginRunner:
    def __init__(self):
        self.plugin_manager = PluginManager()

    def run(self, plugin_name):
        plugin = self.plugin_manager.plugins.get(plugin_name)

        if not plugin:
            raise ValueError(f'Plugin not found: {plugin_name}')

        plugin.start()
