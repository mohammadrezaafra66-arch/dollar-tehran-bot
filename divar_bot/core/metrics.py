class MetricsRegistry:
    def __init__(self):
        self.metrics = {
            'jobs_processed': 0,
            'jobs_failed': 0,
            'queue_depth': 0,
            'extraction_results': 0,
        }

    def increment(self, metric_name, value=1):
        self.metrics[metric_name] = self.metrics.get(metric_name, 0) + value

    def set(self, metric_name, value):
        self.metrics[metric_name] = value

    def snapshot(self):
        return self.metrics
