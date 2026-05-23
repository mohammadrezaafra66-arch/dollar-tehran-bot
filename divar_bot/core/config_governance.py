import hashlib
import json
from datetime import datetime
from pathlib import Path


class ConfigGovernance:
    def __init__(self, audit_path='logs/config_audit.jsonl'):
        self.audit_path = Path(audit_path)
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)

    def fingerprint(self, config):
        serialized = json.dumps(config, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

    def record_loaded(self, config_name, config, trace_context=None):
        entry = {
            'event': 'config_loaded',
            'config_name': config_name,
            'fingerprint': self.fingerprint(config),
            'loaded_at': datetime.utcnow().isoformat(),
            'trace': trace_context.to_log_context() if trace_context else {},
        }

        with self.audit_path.open('a', encoding='utf-8') as file:
            file.write(json.dumps(entry, ensure_ascii=False) + '\n')

        return entry

    def record_decision(self, decision_name, decision_value, source='config', trace_context=None):
        entry = {
            'event': 'runtime_decision',
            'decision_name': decision_name,
            'decision_value': decision_value,
            'source': source,
            'recorded_at': datetime.utcnow().isoformat(),
            'trace': trace_context.to_log_context() if trace_context else {},
        }

        with self.audit_path.open('a', encoding='utf-8') as file:
            file.write(json.dumps(entry, ensure_ascii=False) + '\n')

        return entry
