# app/database.py - نسخه کامل با متد add_website_extraction
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict
from contextlib import contextmanager
from app.config import Config
import json

class Database:
    def __init__(self, db_path: str = None):
        print("📀 Database instance created")
        if db_path is None:
            db_path = Config.DATABASE_PATH
        self.db_path = db_path
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
    
    def _init_tables(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # جدول search_sources
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    city TEXT,
                    province TEXT,
                    keyword TEXT,
                    brand TEXT,
                    related_keywords TEXT,
                    category TEXT,
                    active BOOLEAN DEFAULT 1,
                    priority INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول generated_queries
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS generated_queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id INTEGER,
                    query_text TEXT UNIQUE,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    executed_at TIMESTAMP,
                    FOREIGN KEY (source_id) REFERENCES search_sources(id)
                )
            ''')
            
            # جدول businesses
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS businesses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_id INTEGER,
                    name TEXT,
                    slug TEXT UNIQUE,
                    clean_href TEXT,
                    phone TEXT,
                    website TEXT,
                    address TEXT,
                    city TEXT,
                    province TEXT,
                    rating REAL,
                    reviews_count INTEGER,
                    hours TEXT,
                    place_id TEXT,
                    status TEXT DEFAULT 'pending',
                    retry_count INTEGER DEFAULT 0,
                    last_error TEXT,
                    extracted_at TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول website_extractions
            cursor.execute('''
    CREATE TABLE IF NOT EXISTS website_extractions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        business_id INTEGER,
        email TEXT,
        instagram TEXT,
        telegram TEXT,
        whatsapp TEXT,
        extra_phones TEXT,
        contact_page_url TEXT,
        about_page_url TEXT,
        crawl_status TEXT DEFAULT 'pending',
        crawl_error TEXT,
        crawled_at TIMESTAMP,
        FOREIGN KEY (business_id) REFERENCES businesses(id)
    )
''')
            
            # ایندکس‌ها
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_generated_queries_status ON generated_queries(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_businesses_status ON businesses(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_businesses_slug ON businesses(slug)')
    
    # ========== Search Sources ==========
    
    def add_search_source(self, data: Dict) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO search_sources 
                (city, province, keyword, brand, related_keywords, category, active, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('city'), data.get('province'), data.get('keyword'),
                data.get('brand'), data.get('related_keywords'), data.get('category'),
                data.get('active', 1), data.get('priority', 0)
            ))
            return cursor.lastrowid
    
    # ========== Generated Queries ==========
    
    def add_generated_query(self, source_id: int, query_text: str) -> int:
         """
         اضافه کردن query فقط در صورتی که قبلاً نبوده باشد.
         Returns: id موجود یا جدید
         """
         with self._get_connection() as conn:
             cursor = conn.cursor()
             # اول ببین وجود دارد؟
             cursor.execute('SELECT id FROM generated_queries WHERE query_text = ?', (query_text,))
             existing = cursor.fetchone()
             
             if existing:
                 print(f"  ⏭️ Query already exists (id={existing[0]}): {query_text[:60]}")
                 return existing[0]
             # اضافه کردن جدید
             cursor.execute('''
                            INSERT INTO generated_queries (source_id, query_text, status)
                            VALUES (?, ?, 'pending')
                            ''', (source_id, query_text))
             new_id = cursor.lastrowid
             print(f"  ✅ New query added (id={new_id}): {query_text[:60]}")
             return new_id    
    def get_pending_queries(self, limit: int = None) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if limit:
                cursor.execute('''
                    SELECT id, query_text, source_id
                    FROM generated_queries 
                    WHERE status = 'pending' 
                    ORDER BY id 
                    LIMIT ?
                ''', (limit,))
            else:
                cursor.execute('''
                    SELECT id, query_text, source_id
                    FROM generated_queries 
                    WHERE status = 'pending' 
                    ORDER BY id
                ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def mark_query_done(self, query_id: int):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE generated_queries SET status = 'done', executed_at = ? WHERE id = ?
            ''', (datetime.now().isoformat(), query_id))
    
    # ========== Businesses ==========
    
    def add_businesses_batch(self, query_id: int, businesses: List[Dict]):
        """اضافه کردن یا به‌روزرسانی هوشمند بیزینس‌ها (گزینه C + quality-aware)"""
        from datetime import datetime
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            for biz in businesses:
                slug = biz.get('slug')
                name = biz.get('name')
                clean_href = biz.get('clean_href')
                phone = biz.get('phone', '')
                website = biz.get('website', '')
                address = biz.get('address', '')
                
                # بررسی وجود بیزینس
                cursor.execute('SELECT id, phone, website, address, status FROM businesses WHERE slug = ?', (slug,))
                existing = cursor.fetchone()
                
                if existing:
                    business_id = existing[0]
                    old_phone = existing[1] or ""
                    old_website = existing[2] or ""
                    old_address = existing[3] or ""
                    old_status = existing[4]
                    
                    # تصمیم‌گیری برای به‌روزرسانی (گزینه C + quality-aware)
                    update_phone = (not old_phone and phone) or (phone and len(phone) > len(old_phone))
                    update_website = (not old_website and website) or (website and len(website) > len(old_website))
                    update_address = (not old_address and address) or (address and len(address) > len(old_address))
                    
                    if update_phone or update_website or update_address:
                        final_phone = phone if update_phone else old_phone
                        final_website = website if update_website else old_website
                        final_address = address if update_address else old_address
                        
                        cursor.execute('''
                            UPDATE businesses 
                            SET phone = ?,
                                website = ?,
                                address = ?,
                                last_seen_at = CURRENT_TIMESTAMP,
                                updated_at = ?
                            WHERE id = ?
                        ''', (final_phone, final_website, final_address, datetime.now().isoformat(), business_id))
                        print(f"  🔄 Updated business: {name[:40]}...")
                    else:
                        # فقط last_seen_at را به‌روز کن
                        cursor.execute('''
                            UPDATE businesses SET last_seen_at = CURRENT_TIMESTAMP, updated_at = ? WHERE id = ?
                        ''', (datetime.now().isoformat(), business_id))
                else:
                    # اضافه کردن جدید
                    cursor.execute('''
                        INSERT INTO businesses 
                        (query_id, name, slug, clean_href, phone, website, address, 
                         status, data_source, last_seen_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', 'google_maps', CURRENT_TIMESTAMP, ?)
                    ''', (query_id, name, slug, clean_href, phone, website, address, datetime.now().isoformat()))
                    print(f"  ✅ New business added: {name[:40]}...")    
    def get_next_business_for_processing(self, limit=None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, slug, clean_href, query_id, retry_count
                FROM businesses 
                WHERE status = 'failed' AND retry_count < 3
                ORDER BY retry_count, id
                LIMIT 1
            """)
            row = cursor.fetchone()
            
            if row:
                return [dict(row)]
            
            if limit:
                cursor.execute("""
                    SELECT id, name, slug, clean_href, query_id
                    FROM businesses 
                    WHERE status = 'pending'
                    ORDER BY id
                    LIMIT ?
                """, (limit,))
            else:
                cursor.execute("""
                    SELECT id, name, slug, clean_href, query_id
                    FROM businesses 
                    WHERE status = 'pending'
                    ORDER BY id
                """)
            return [dict(row) for row in cursor.fetchall()]
    
    def mark_success(self, business_id: int, phone: str = '', website: str = '', address: str = ''):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE businesses 
                SET status = 'done', 
                    phone = ?, website = ?, address = ?,
                    updated_at = ?
                WHERE id = ?
            ''', (phone, website, address, datetime.now().isoformat(), business_id))
    
    def mark_failed(self, business_id: int, error: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE businesses 
                SET status = 'failed', 
                    retry_count = retry_count + 1,
                    last_error = ?,
                    updated_at = ?
                WHERE id = ?
            ''', (error, datetime.now().isoformat(), business_id))
    
    def reset_processing_to_pending(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE businesses 
                SET status = 'pending', 
                    last_error = 'Reset by system',
                    updated_at = ?
                WHERE status = 'processing'
            """, (datetime.now().isoformat(),))
            return cursor.rowcount
    
    def add_website_extraction(self, business_id: int, data: dict):
        """ذخیره اطلاعات استخراج شده از وبسایت"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO website_extractions 
                (business_id, email, instagram, telegram, whatsapp, 
                 contact_page_url, about_page_url, extracted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                business_id,
                data.get('email', ''),
                data.get('instagram', ''),
                data.get('telegram', ''),
                data.get('whatsapp', ''),
                data.get('contact_page_url', ''),
                data.get('about_page_url', ''),
                datetime.now().isoformat()
            ))
            return cursor.lastrowid
    
    def get_all_done_businesses(self) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT name, phone, website, address
                FROM businesses 
                WHERE status = 'done'
                ORDER BY id
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_stats(self) -> Dict:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM businesses')
            total = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM businesses WHERE status = "done"')
            done = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM businesses WHERE status = "failed"')
            failed = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM businesses WHERE status = "pending"')
            pending = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM businesses WHERE phone != "" AND phone IS NOT NULL')
            phones = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM businesses WHERE website != "" AND website IS NOT NULL')
            websites = cursor.fetchone()[0]
            
            return {
                'total': total,
                'done': done,
                'failed': failed,
                'pending': pending,
                'phones': phones,
                'websites': websites
            }
    
    def close(self):
        pass