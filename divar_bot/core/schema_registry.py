class SchemaRegistry:
    def __init__(self):
        self.schemas = {}

    def register(self, schema_name, schema_definition):
        self.schemas[schema_name] = schema_definition

    def get(self, schema_name):
        return self.schemas.get(schema_name)

    def validate(self, schema_name, payload):
        schema = self.schemas.get(schema_name)

        if not schema:
            return False

        required_fields = schema.get('required', [])

        for field in required_fields:
            if field not in payload:
                return False

        return True
