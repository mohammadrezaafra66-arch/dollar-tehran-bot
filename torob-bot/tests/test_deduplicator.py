import unittest

from app.deduplicator import Deduplicator


class DeduplicatorTests(unittest.TestCase):
    def test_merges_only_on_shared_phone_or_domain(self):
        sellers = [
            {"name": "A", "phone": "09120000000", "store_url": "https://shop.example.com"},
            {"name": "B", "phone": "09120000000", "store_url": "https://shop2.example.com"},
            {"name": "C", "phone": "09121111111", "store_url": "https://shop3.example.com"},
            {"name": "D", "phone": "", "store_url": "https://torob.com/p/abc"},
            {"name": "E", "phone": "", "store_url": "https://shop4.example.com"},
        ]

        unique, duplicates = Deduplicator.deduplicate(sellers)

        self.assertEqual(len(unique), 4)
        self.assertEqual(duplicates, 1)
        self.assertEqual(unique[0]["name"], "A")
        self.assertEqual(unique[1]["name"], "C")
        self.assertEqual(unique[2]["name"], "D")
        self.assertEqual(unique[3]["name"], "E")


if __name__ == "__main__":
    unittest.main()
