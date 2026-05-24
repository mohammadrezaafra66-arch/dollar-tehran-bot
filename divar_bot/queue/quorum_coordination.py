class QuorumCoordinator:
    def __init__(self, redis_client, namespace='afra:quorum'):
        self.redis = redis_client
        self.namespace = namespace

    def vote(self, topic, voter_id, value='yes'):
        self.redis.hset(f'{self.namespace}:{topic}', voter_id, value)

    def tally(self, topic):
        votes = self.redis.hgetall(f'{self.namespace}:{topic}')

        yes_votes = len([v for v in votes.values() if v == 'yes'])
        no_votes = len([v for v in votes.values() if v == 'no'])

        return {
            'yes': yes_votes,
            'no': no_votes,
            'total': len(votes),
        }
