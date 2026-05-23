class PluginManager:
    def __init__(self):
        self.plugins = {}

    def register(self, name, plugin):
        self.plugins[name] = plugin

    def list_plugins(self):
        return list(self.plugins.keys())
