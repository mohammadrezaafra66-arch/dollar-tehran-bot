class AdaptiveThrottling:
    def __init__(self, minimum_delay=1, maximum_delay=30):
        self.minimum_delay = minimum_delay
        self.maximum_delay = maximum_delay

    def delay_for(self, queue_depth, failure_rate=0):
        delay = self.minimum_delay

        if queue_depth > 1000:
            delay += 5

        if queue_depth > 5000:
            delay += 10

        if failure_rate > 0.1:
            delay += 5

        return min(delay, self.maximum_delay)
