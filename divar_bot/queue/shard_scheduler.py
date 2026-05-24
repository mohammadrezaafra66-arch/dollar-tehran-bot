import hashlib


class ShardAwareScheduler:
    def __init__(self, total_shards=8):
        self.total_shards = total_shards

    def shard_for(self, key):
        digest = hashlib.sha256(str(key).encode()).hexdigest()
        return int(digest, 16) % self.total_shards

    def stream_name_for(self, base_stream, shard_key):
        shard = self.shard_for(shard_key)
        return f'{base_stream}:shard:{shard}'
