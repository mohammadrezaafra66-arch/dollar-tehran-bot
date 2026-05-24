class QueueMetrics:
    def __init__(self, redis_client, stream_name='afra:jobs'):
        self.redis = redis_client
        self.stream_name = stream_name

    def snapshot(self):
        info = self.redis.xinfo_stream(self.stream_name)

        return {
            'length': info.get('length', 0),
            'radix_tree_keys': info.get('radix-tree-keys', 0),
            'groups': info.get('groups', 0),
            'last_generated_id': info.get('last-generated-id'),
        }
