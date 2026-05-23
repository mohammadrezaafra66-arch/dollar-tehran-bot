import random
import time


class SpeedProfileRuntime:
    def __init__(self, profiles=None):
        self.profiles = profiles or {
            'safe': {'delay': [20, 60]},
            'slow': {'delay': [10, 25]},
            'normal': {'delay': [5, 12]},
            'fast': {'delay': [1, 4]},
            'test': {'delay': [0, 1]},
        }

    def get_profile(self, name):
        return self.profiles.get(name, self.profiles['safe'])

    def sleep(self, profile_name='safe'):
        profile = self.get_profile(profile_name)
        min_delay, max_delay = profile.get('delay', [20, 60])
        time.sleep(random.uniform(min_delay, max_delay))
