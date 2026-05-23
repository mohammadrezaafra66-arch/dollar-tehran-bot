class Job:
    def __init__(self, job_type, plugin_name, payload, priority=5, status='pending'):
        self.job_type = job_type
        self.plugin_name = plugin_name
        self.payload = payload
        self.priority = priority
        self.status = status


class AuditEvent:
    def __init__(self, action, entity_type, entity_id):
        self.action = action
        self.entity_type = entity_type
        self.entity_id = entity_id
