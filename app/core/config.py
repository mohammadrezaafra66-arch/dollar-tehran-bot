from pathlib import Path


class ConfigLoader:
    def __init__(self, config_path='config/config.yaml'):
        self.config_path = Path(config_path)
        self.config = {}

    def exists(self):
        return self.config_path.exists()
