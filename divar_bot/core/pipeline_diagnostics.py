from collections import defaultdict
from datetime import datetime


class PipelineDiagnostics:
    def __init__(self):
        self.stage_counters = defaultdict(int)
        self.stage_failures = defaultdict(int)
        self.records_impacted = defaultdict(int)
        self.last_failure = None

    def record_stage_start(self, stage_name, records_count=0):
        self.stage_counters[stage_name] += 1
        if records_count:
            self.records_impacted[f'{stage_name}.seen'] += records_count

    def record_stage_success(self, stage_name, records_count=0):
        if records_count:
            self.records_impacted[f'{stage_name}.success'] += records_count

    def record_stage_failure(self, stage_name, error, records_count=1, **context):
        self.stage_failures[stage_name] += 1
        self.records_impacted[f'{stage_name}.failed'] += records_count
        self.last_failure = {
            'stage': stage_name,
            'error': str(error),
            'records_impacted': records_count,
            'context': context,
            'failed_at': datetime.utcnow().isoformat(),
        }

    def snapshot(self):
        return {
            'stage_runs': dict(self.stage_counters),
            'stage_failures': dict(self.stage_failures),
            'records_impacted': dict(self.records_impacted),
            'last_failure': self.last_failure,
        }
