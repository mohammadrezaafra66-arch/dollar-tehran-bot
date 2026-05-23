class DivarParser:
    def normalize(self, extracted_data):
        return {
            'source_url': extracted_data.get('url'),
            'title': extracted_data.get('title'),
            'raw_payload': extracted_data
        }
