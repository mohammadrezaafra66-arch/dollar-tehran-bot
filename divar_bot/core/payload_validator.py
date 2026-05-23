class PayloadValidator:
    def __init__(self, required_fields=None):
        self.required_fields = required_fields or ['url']

    def validate(self, payload):
        if not isinstance(payload, dict):
            return {
                'valid': False,
                'error': 'payload_must_be_object',
                'missing_fields': self.required_fields,
            }

        missing = [field for field in self.required_fields if not payload.get(field)]

        return {
            'valid': len(missing) == 0,
            'error': None if not missing else 'missing_required_fields',
            'missing_fields': missing,
        }
