class PipelineMetrics:
    def __init__(self):
        self.metrics = {
            'pipeline_stage_failures': 0,
            'pipeline_records_failed': 0,
            'pipeline_records_processed': 0,
            'pipeline_records_saved': 0,
        }

    def increment(self, metric_name, value=1):
        self.metrics[metric_name] = self.metrics.get(metric_name, 0) + value

    def snapshot(self):
        return self.metrics
