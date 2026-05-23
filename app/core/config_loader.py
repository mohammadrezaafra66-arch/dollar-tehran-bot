from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml


class ConfigLoader:
    def __init__(self, config_path: str | Path = 'config/config.yaml'):
        self.config_path = Path(config_path)
        self.config: dict[str, Any] = {}

    def load(self) -> dict[str, Any]:
        if not self.config_path.exists():
            raise FileNotFoundError(f'Config file not found: {self.config_path}')

        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f) or {}

        return self.config

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def validate(self) -> bool:
        required_keys = ['database', 'workers', 'logging']
        missing = [k for k in required_keys if k not in self.config]

        if missing:
            raise ValueError(f'Missing config keys: {missing}')

        return True
