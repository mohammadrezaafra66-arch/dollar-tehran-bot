# app/query_generator.py
import pandas as pd
import json
from typing import List, Dict
from app.database import Database
import os

class QueryGenerator:
    """ساخت و مدیریت کوئری‌های جستجو از فایل Excel"""
    
    def __init__(self, input_file='input/google_maps_input.xlsx'):
        self.input_file = input_file
        self.db = Database()
    
    def load_sources(self) -> List[Dict]:
        """بارگذاری منابع از فایل Excel"""
        if not os.path.exists(self.input_file):
            print(f"❌ Input file not found: {self.input_file}")
            return []
        
        df = pd.read_excel(self.input_file)
        
        # فقط ردیف‌های فعال
        active_sources = df[df['active'] == 1]
        
        sources = []
        for _, row in active_sources.iterrows():
            source = {
                'city': str(row.get('شهر', '')).strip(),
                'province': str(row.get('استان', '')).strip(),
                'keyword': str(row.get('کلمه اصلی', '')).strip(),
                'brand': str(row.get('برند', '')).strip(),
                'related_keywords': str(row.get('کلمات مرتبط', '')).strip(),
                'category': str(row.get('دسته بندی', '')).strip(),
                'active': int(row.get('active', 1))
            }
            sources.append(source)
        
        return sources
    
    def generate_queries_from_source(self, source: Dict) -> List[str]:
        """تولید کوئری از یک منبع"""
        queries = []
        
        keyword = source['keyword']
        city = source['city']
        province = source['province']
        brand = source['brand']
        related = source['related_keywords']

        # ترکیب 1: کلمه اصلی + شهر
        if keyword and city:
            queries.append(f"{keyword} در {city}")
        
        # ترکیب 2: کلمه اصلی + استان
        if keyword and province:
            queries.append(f"{keyword} در {province}")
        
        # ترکیب 3: برند + کلمه اصلی
        if brand and brand != 'nan' and brand != '' and keyword:
            queries.append(f"{brand} {keyword}")
        
        # ترکیب 4: برند + کلمه اصلی + شهر
        if brand and keyword and city:
            queries.append(f"{brand} {keyword} در {city}")
        
        # ترکیب 5: کلمات مرتبط + شهر
        if related and city:
            related_list = [r.strip() for r in related.split(',')]
            for r in related_list[:3]:  # حداکثر 3 کلمه مرتبط
                if r:
                    queries.append(f"{r} در {city}")
        
        # حذف تکراری‌ها
        return list(set(queries))
    
    def save_source_to_db(self, source: Dict, queries: List[str]) -> int:
        """ذخیره منبع و کوئری‌ها در دیتابیس"""
        # ذخیره منبع
        source_id = self.db.add_search_source(source)
        
        if source_id:
            # ذخیره کوئری‌ها
            for query in queries:
                self.db.add_generated_query(source_id, query)
                print(f"  📝 Added query: {query}")
        
        return source_id
    
    def run(self):
        """اجرای کامل تولید و ذخیره کوئری‌ها"""
        print("=" * 60)
        print("📍 Query Generator")
        print("=" * 60)
        
        sources = self.load_sources()
        
        if not sources:
            print("❌ No active sources found!")
            return []
        
        print(f"📋 Found {len(sources)} active sources")
        
        all_queries = []
        
        for src in sources:
            print(f"\n🔍 Processing: {src.get('keyword')} - {src.get('city')}")
            queries = self.generate_queries_from_source(src)
            
            if queries:
                self.save_source_to_db(src, queries)
                all_queries.extend(queries)
                print(f"  ✅ Generated {len(queries)} queries")
            else:
                print(f"  ⚠️ No queries generated")
        
        # نمایش آمار نهایی
        pending = self.db.get_pending_queries()
        print(f"\n📊 Total generated queries: {len(all_queries)}")
        print(f"📊 Pending queries in DB: {len(pending)}")
        
        self.db.close()
        return all_queries

if __name__ == "__main__":
    generator = QueryGenerator()
    generator.run()