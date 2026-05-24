from __future__ import annotations

import logging
from pathlib import Path
from datetime import datetime


class PlatformLogger:
    def __init__(self, activity_file: str = 'logs/activity.log', error_file: str = 'logs/error.log'):
        self.activity_file = Path(activity_file)
        self.error_file = Path(error_file)
        self.activity_file.parent.mkdir(parents=True, exist_ok=True)
        self.error_file.parent.mkdir(parents=True, exist_ok=True)

        self.activity_logger = logging.getLogger('afra_activity')
        self.error_logger = logging.getLogger('afra_error')

        self.activity_logger.setLevel(logging.INFO)
        self.error_logger.setLevel(logging.ERROR)

        if not self.activity_logger.handlers:
            activity_handler = logging.FileHandler(self.activity_file, encoding='utf-8')
            activity_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
            self.activity_logger.addHandler(activity_handler)

        if not self.error_logger.handlers:
            error_handler = logging.FileHandler(self.error_file, encoding='utf-8')
            error_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
            self.error_logger.addHandler(error_handler)

    def activity(self, message: str, **extra):
        payload = self._format(message, extra)
        self.activity_logger.info(payload)

    def error(self, message: str, **extra):
        payload = self._format(message, extra)
        self.error_logger.error(payload)

    @staticmethod
    def _format(message: str, extra: dict) -> str:
        if not extra:
            return message
        meta = ' | '.join(f'{key}={value}' for key, value in extra.items())
        return f'{message} | {meta}'

    def run_started(self, bot_name: str):
        self.activity('run_started', bot=bot_name, time=datetime.now().isoformat())

    def run_finished(self, bot_name: str):
        self.activity('run_finished', bot=bot_name, time=datetime.now().isoformat())
