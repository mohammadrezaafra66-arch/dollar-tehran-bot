from __future__ import annotations


class CredentialMetrics:
    def __init__(self):
        self.counters: dict[str, int] = {}

    def increment(self, key: str) -> None:
        self.counters[key] = self.counters.get(key, 0) + 1
