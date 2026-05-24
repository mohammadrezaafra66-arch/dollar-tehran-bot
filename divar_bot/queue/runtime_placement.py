class RuntimePlacementStrategy:
    def select(self, workers, shard_key=None):
        active = [worker for worker in workers if worker.get('status') == 'active']

        if not active:
            return None

        if shard_key:
            return active[hash(shard_key) % len(active)]

        return sorted(active, key=lambda item: int(item.get('capacity', 1)), reverse=True)[0]
