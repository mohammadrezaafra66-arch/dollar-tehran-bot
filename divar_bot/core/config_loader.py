from pathlib import Path

import yaml

from divar_bot.core.config_validator import ConfigValidator


class ConfigLoader:
    def __init__(self, validator=None):
        self.validator = validator or ConfigValidator()

    def load(self, config_path):
        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(f'Config file not found: {config_path}')

        with config_file.open('r', encoding='utf-8') as file:
            config = yaml.safe_load(file) or {}

        validation = self.validator.validate(config)

        if not validation['valid']:
            raise ValueError(
                f"Invalid runtime config. Missing sections: {validation['missing_sections']}"
            )

        return config
