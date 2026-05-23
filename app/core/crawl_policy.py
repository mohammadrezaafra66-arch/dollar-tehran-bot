class CrawlPolicy:
    def __init__(self, max_pages=10, max_ads=100):
        self.max_pages = max_pages
        self.max_ads = max_ads

    def can_continue_pages(self, current_page):
        return current_page < self.max_pages

    def can_continue_ads(self, current_count):
        return current_count < self.max_ads
