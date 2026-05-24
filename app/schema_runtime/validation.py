class SchemaValidationRuntime:
    def __init__(self):
        self._schemas = {}

    def register(
        self,
        schema_name: str,
        required_fields=None,
    ):
        required_fields = required_fields or []

        self._schemas[schema_name] = {
            "required_fields": required_fields,
        }

    def validate(
        self,
        schema_name: str,
        payload: dict,
    ):
        schema = self._schemas.get(schema_name)

        if not schema:
            return {
                "valid": False,
                "errors": ["schema_not_found"],
            }

        errors = []

        for field in schema["required_fields"]:
            if field not in payload:
                errors.append(
                    f"missing_field:{field}"
                )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }
