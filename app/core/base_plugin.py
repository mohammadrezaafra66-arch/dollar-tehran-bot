class BasePlugin:
    name = 'base_plugin'

    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def validate_config(self, config):
        return True
