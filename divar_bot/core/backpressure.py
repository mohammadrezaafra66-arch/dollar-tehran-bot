class BackpressureManager:
    def __init__(self, max_queue_depth=1000):
        self.max_queue_depth = max_queue_depth

    def should_throttle(self, current_queue_depth):
        return current_queue_depth >= self.max_queue_depth

    def recommended_delay_seconds(self, current_queue_depth):
        if current_queue_depth >= self.max_queue_depth:
            return 30

        if current_queue_depth >= int(self.max_queue_depth * 0.8):
            return 10

        return 0
