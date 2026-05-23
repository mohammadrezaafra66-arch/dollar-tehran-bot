class JobStateMachine:
    ALLOWED_TRANSITIONS = {
        'pending': {'running', 'cancelled'},
        'running': {'completed', 'failed', 'retrying', 'cancelled'},
        'retrying': {'pending', 'dead_letter'},
        'failed': {'retrying', 'dead_letter'},
        'completed': set(),
        'cancelled': set(),
        'dead_letter': set(),
    }

    def can_transition(self, current_state, next_state):
        return next_state in self.ALLOWED_TRANSITIONS.get(current_state, set())

    def transition(self, current_state, next_state):
        if not self.can_transition(current_state, next_state):
            raise ValueError(f'Invalid job transition: {current_state} -> {next_state}')

        return next_state
