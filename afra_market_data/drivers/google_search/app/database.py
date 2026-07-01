# app/database.py - Google Search Driver
import sqlite3
from datetime import datetime
from typing import List, Dict
from contextlib import contextmanager
from app.config import Config


class Database:
    def __init__(self, db_path: str = None):
        print("Database instance created")
        self.db_path = db_path or Config.DATABASE_PATH
        self._init_tables()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _table_columns(self, cursor, table_name):
        cursor.execute(f"PRAGMA table_info({table_name})")
        return {row[1] for row in cursor.fetchall()}

    def _ensure_column(self, cursor, table_name, column_name, column_sql):
        if column_name not in self._table_columns(cursor, table_name):
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}")
            print(f"DB migrated: added {table_name}.{column_name}")

    def _init_tables(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    city TEXT, province TEXT, keyword TEXT, brand TEXT,
                    related_keywords TEXT, category TEXT,
                    active BOOLEAN DEFAULT 1, priority INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS generated_queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id INTEGER, query_text TEXT UNIQUE,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    executed_at TIMESTAMP,
                    FOREIGN KEY (source_id) REFERENCES search_sources(id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS businesses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_id INTEGER,
                    name TEXT,
                    result_url TEXT UNIQUE,
                    result_snippet TEXT,
                    phone TEXT,
                    website TEXT,
                    address TEXT,
                    city TEXT,
                    province TEXT,
                    data_source TEXT DEFAULT 'google_search',
                    status TEXT DEFAULT 'pending',
                    sync_status TEXT DEFAULT 'pending',
                    retry_count INTEGER DEFAULT 0,
                    last_error TEXT,
                    extracted_at TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self._ensure_column(cursor, 'businesses', 'phone_mobile', 'TEXT DEFAULT ""')
            self._ensure_column(cursor, 'businesses', 'phone_landline', 'TEXT DEFAULT ""')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS website_extractions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    business_id INTEGER,
                    email TEXT, instagram TEXT, telegram TEXT, whatsapp TEXT,
                    extra_phones TEXT, contact_page_url TEXT, about_page_url TEXT,
                    crawl_status TEXT DEFAULT 'pending',
                    crawl_error TEXT, crawled_at TIMESTAMP, extracted_at TIMESTAMP,
                    FOREIGN KEY (business_id) REFERENCES businesses(id)
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_gq_status ON generated_queries(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_biz_status ON businesses(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_biz_url ON businesses(result_url)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_biz_sync ON businesses(sync_status)')

    def add_search_source(self, data: Dict) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO search_sources
                (city, province, keyword, brand, related_keywords, category, active, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (data.get('city'), data.get('province'), data.get('keyword'),
                  data.get('brand'), data.get('related_keywords'), data.get('category'),
                  data.get('active', 1), data.get('priority', 0)))
            return cursor.lastrowid

    def add_generated_query(self, source_id: int, query_text: str) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM generated_queries WHERE query_text = ?', (query_text,))
            existing = cursor.fetchone()
            if existing:
                return existing[0]
            cursor.execute('INSERT INTO generated_queries (source_id, query_text, status) VALUES (?, ?, "pending")',
                           (source_id, query_text))
            return cursor.lastrowid

    def get_pending_queries(self, limit: int = None) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            q = 'SELECT id, query_text, source_id FROM generated_queries WHERE status = "pending" ORDER BY id'
            cursor.execute(q + (f' LIMIT {limit}' if limit else ''))
            return [dict(row) for row in cursor.fetchall()]

    def mark_query_done(self, query_id: int):
        with self._get_connection() as conn:
            conn.execute('UPDATE generated_queries SET status = "done", executed_at = ? WHERE id = ?',
                         (datetime.now().isoformat(), query_id))

    def add_results_batch(self, query_id: int, results: List[Dict]):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for r in results:
                url = r.get('result_url', '')
                if not url:
                    continue
                cursor.execute('SELECT id, phone, website FROM businesses WHERE result_url = ?', (url,))
                existing = cursor.fetchone()
                if existing:
                    biz_id, old_phone, old_website = existing[0], existing[1] or '', existing[2] or ''
                    new_phone, new_website = r.get('phone', ''), r.get('website', '')
                    if (not old_phone and new_phone) or (not old_website and new_website):
                        cursor.execute(
                            'UPDATE businesses SET phone = ?, website = ?, updated_at = ? WHERE id = ?',
                            (new_phone or old_phone, new_website or old_website,
                             datetime.now().isoformat(), biz_id))
                else:
                    cursor.execute('''
                        INSERT INTO businesses
                        (query_id, name, result_url, result_snippet, phone, website,
                         address, city, province, status, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                    ''', (query_id, r.get('name', ''), url, r.get('result_snippet', ''),
                          r.get('phone', ''), r.get('website', url),
                          r.get('address', ''), r.get('city', ''), r.get('province', ''),
                          datetime.now().isoformat()))

    def get_next_for_processing(self, limit: int = 1) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, result_url, website, query_id, retry_count
                FROM businesses WHERE status = 'failed' AND retry_count < 3
                ORDER BY retry_count, id LIMIT 1
            ''')
            row = cursor.fetchone()
            if row:
                return [dict(row)]
            cursor.execute('''
                SELECT id, name, result_url, website, query_id, retry_count
                FROM businesses WHERE status = 'pending' ORDER BY id LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def mark_success(self, business_id: int, phone: str = '', website: str = '', address: str = ''):
        with self._get_connection() as conn:
            conn.execute('''
                UPDATE businesses
                SET status = 'done',
                    phone = CASE WHEN ? != '' THEN ? ELSE phone END,
                    website = CASE WHEN ? != '' THEN ? ELSE website END,
                    address = CASE WHEN ? != '' THEN ? ELSE address END,
                    extracted_at = ?, updated_at = ?
                WHERE id = ?
            ''', (phone, phone, website, website, address, address,
                  datetime.now().isoformat(), datetime.now().isoformat(), business_id))

    def mark_failed(self, business_id: int, error: str):
        with self._get_connection() as conn:
            conn.execute('''
                UPDATE businesses SET status = 'failed', retry_count = retry_count + 1,
                last_error = ?, updated_at = ? WHERE id = ?
            ''', (error, datetime.now().isoformat(), business_id))

    def add_website_extraction(self, business_id: int, data: dict):
        with self._get_connection() as conn:
            conn.execute('''
                INSERT INTO website_extractions
                (business_id, email, instagram, telegram, whatsapp,
                 extra_phones, contact_page_url, about_page_url, extracted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (business_id, data.get('email',''), data.get('instagram',''),
                  data.get('telegram',''), data.get('whatsapp',''), data.get('extra_phones',''),
                  data.get('contact_page_url',''), data.get('about_page_url',''),
                  datetime.now().isoformat()))

    def get_stats(self) -> Dict:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            stats = {}
            for key, q in [
                ('total',   'SELECT COUNT(*) FROM businesses'),
                ('done',    'SELECT COUNT(*) FROM businesses WHERE status = "done"'),
                ('failed',  'SELECT COUNT(*) FROM businesses WHERE status = "failed"'),
                ('pending', 'SELECT COUNT(*) FROM businesses WHERE status = "pending"'),
                ('synced',  'SELECT COUNT(*) FROM businesses WHERE sync_status = "synced"'),
            ]:
                cursor.execute(q)
                stats[key] = cursor.fetchone()[0]
            return stats

    def close(self):
        pass

    def get_source(self, source_id: int) -> Dict:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT city, province, keyword FROM search_sources WHERE id = ?',
                (source_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else {}

    def mark_query_businesses_done(self, query_id: int):
        """بعد از collect، همه pending این query رو done بزن تا website_crawler بگیره"""
        with self._get_connection() as conn:
            conn.execute(
                'UPDATE businesses SET status = "done" WHERE query_id = ? AND status = "pending"',
                (query_id,)
            )
