class ConfigValidator:
    REQUIRED_SECTIONS = [
        'environment',
        'queue',
        'browser',
        'plugins',
        'speed_profiles',
    ]

    def validate(self, config):
        missing = []

        for section in self.REQUIRED_SECTIONS:
            if section not in config:
                missing.append(section)

        return {
            'valid': len(missing) == 0,
            'missing_sections': missing,
        }
