import json
import logging
from datetime import datetime


class StructuredLogger:
    def __init__(self, name='divar_bot'):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(handler)

    def log(self, level, event, **context):
        payload = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level,
            'event': event,
            'context': context,
        }

        message = json.dumps(payload, ensure_ascii=False)

        if level == 'error':
            self.logger.error(message)
        elif level == 'warning':
            self.logger.warning(message)
        else:
            self.logger.info(message)

    def info(self, event, **context):
        self.log('info', event, **context)

    def warning(self, event, **context):
        self.log('warning', event, **context)

    def error(self, event, **context):
        self.log('error', event, **context)
