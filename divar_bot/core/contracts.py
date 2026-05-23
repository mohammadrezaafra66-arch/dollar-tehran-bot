from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class QueueBackend(ABC):
    @abstractmethod
    def get_next_job(self) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def complete_job(self, job_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def fail_job(self, job_id: str, error_message: str) -> None:
        raise NotImplementedError


class PluginBackend(ABC):
    @abstractmethod
    def get_plugin(self, plugin_name: str):
        raise NotImplementedError


class ResultBackend(ABC):
    @abstractmethod
    def save(self, plugin_name: str, data: Dict[str, Any]) -> None:
        raise NotImplementedError


class LoggerBackend(ABC):
    @abstractmethod
    def info(self, event: str, **context) -> None:
        raise NotImplementedError

    @abstractmethod
    def error(self, event: str, **context) -> None:
        raise NotImplementedError
