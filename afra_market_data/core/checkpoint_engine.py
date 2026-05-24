from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class CheckpointEngine:
    def __init__(self, checkpoint_path: str = 'data/checkpoints/state.json'):
        self.checkpoint_path = Path(checkpoint_path)
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, payload: dict[str, Any]):
        with open(self.checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def load(self) -> dict[str, Any]:
        if not self.checkpoint_path.exists():
            return {}

        with open(self.checkpoint_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def clear(self):
        if self.checkpoint_path.exists():
            self.checkpoint_path.unlink()
