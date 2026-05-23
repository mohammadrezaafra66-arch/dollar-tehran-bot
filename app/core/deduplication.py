class DeduplicationEngine:
    def is_duplicate_ad(self, repository, source_url):
        existing = repository.find_by_source_url(source_url)
        return existing is not None

    def normalize_text(self, value):
        if not value:
            return ''

        return value.strip().lower()
