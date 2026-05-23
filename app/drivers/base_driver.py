from __future__ import annotations

from abc import ABC, abstractmethod


class BaseDriver(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def start(self):
        raise NotImplementedError

    @abstractmethod
    async def stop(self):
        raise NotImplementedError

    @abstractmethod
    async def process(self, payload: dict):
        raise NotImplementedError
