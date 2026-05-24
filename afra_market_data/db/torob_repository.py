from __future__ import annotations

import json

from afra_market_data.db.storage import SQLiteStorage


class TorobRepository:
    def __init__(self, storage: SQLiteStorage | None = None):
        self.storage = storage or SQLiteStorage()
        self._initialize()

    def _initialize(self):
        self.storage.execute('''
            CREATE TABLE IF NOT EXISTS torob_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT,
                product_url TEXT UNIQUE,
                title TEXT,
                page_title TEXT,
                raw_text_sample TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.storage.execute('''
            CREATE TABLE IF NOT EXISTS torob_sellers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_url TEXT,
                seller_name TEXT,
                price_text TEXT,
                warranty_text TEXT,
                seller_url TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

    def save_product(self, query: str, product: dict):
        self.storage.execute(
            '''
            INSERT OR REPLACE INTO torob_products (
                query,
                product_url,
                title,
                page_title,
                raw_text_sample
            ) VALUES (?, ?, ?, ?, ?)
            ''',
            (
                query,
                product.get('url'),
                product.get('title'),
                product.get('page_title'),
                product.get('raw_text_sample'),
            ),
        )

    def save_seller(self, seller: dict):
        self.storage.execute(
            '''
            INSERT INTO torob_sellers (
                product_url,
                seller_name,
                price_text,
                warranty_text,
                seller_url
            ) VALUES (?, ?, ?, ?, ?)
            ''',
            (
                seller.get('product_url'),
                seller.get('seller_name'),
                seller.get('price_text'),
                seller.get('warranty_text'),
                seller.get('seller_url'),
            ),
        )

    def fetch_products(self) -> list[dict]:
        return self.storage.fetch_all(
            'SELECT * FROM torob_products ORDER BY id DESC'
        )

    def fetch_sellers(self) -> list[dict]:
        return self.storage.fetch_all(
            'SELECT * FROM torob_sellers ORDER BY id DESC'
        )
