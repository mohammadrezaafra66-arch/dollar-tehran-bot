-- database_schema_v2.sql
-- نسخه کامل Schema برای پروژه Google Maps Scraper

-- 1. جدول منابع جستجو (از فایل Excel)
CREATE TABLE IF NOT EXISTS search_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city TEXT,
    province TEXT,
    keyword TEXT,
    brand TEXT,
    related_keywords TEXT,  -- JSON array
    category TEXT,
    active BOOLEAN DEFAULT 1,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. جدول عبارات جستجوی تولید شده
CREATE TABLE IF NOT EXISTS generated_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER,
    query_text TEXT UNIQUE,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    executed_at TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES search_sources(id)
);

-- 3. جدول بیزینس‌ها (تکمیل شده)
CREATE TABLE IF NOT EXISTS businesses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_id INTEGER,
    name TEXT,
    slug TEXT UNIQUE,
    phone TEXT,
    website TEXT,
    address TEXT,
    city TEXT,
    province TEXT,
    rating REAL,
    reviews_count INTEGER,
    hours TEXT,
    place_id TEXT,
    lat REAL,
    lng REAL,
    status TEXT DEFAULT 'pending',
    retry_count INTEGER DEFAULT 0,
    last_error TEXT,
    extracted_at TIMESTAMP,
    FOREIGN KEY (query_id) REFERENCES generated_queries(id)
);

-- 4. جدول اطلاعات استخراج شده از سایت
CREATE TABLE IF NOT EXISTS website_extractions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER,
    email TEXT,
    instagram TEXT,
    telegram TEXT,
    whatsapp TEXT,
    products TEXT,  -- JSON array
    brands TEXT,    -- JSON array
    contact_page_url TEXT,
    about_page_url TEXT,
    extracted_at TIMESTAMP,
    FOREIGN KEY (business_id) REFERENCES businesses(id)
);

-- 5. جدول خروجی نهایی برای API افراکالا
CREATE TABLE IF NOT EXISTS final_output (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER,
    query_text TEXT,
    name TEXT,
    phone_mobile TEXT,
    phone_landline TEXT,
    email TEXT,
    city TEXT,
    province TEXT,
    website TEXT,
    instagram TEXT,
    telegram TEXT,
    whatsapp TEXT,
    products TEXT,
    brands TEXT,
    google_rating REAL,
    reviews_count INTEGER,
    place_id TEXT,
    extraction_date TIMESTAMP,
    quality_score TEXT,  -- high, medium, low
    status TEXT DEFAULT 'pending',
    FOREIGN KEY (business_id) REFERENCES businesses(id)
);

-- 6. جدول تکراری‌ها
CREATE TABLE IF NOT EXISTS duplicates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id_1 INTEGER,
    business_id_2 INTEGER,
    match_reason TEXT,
    resolved BOOLEAN DEFAULT 0,
    FOREIGN KEY (business_id_1) REFERENCES businesses(id),
    FOREIGN KEY (business_id_2) REFERENCES businesses(id)
);

-- ایندکس‌ها برای سرعت بیشتر
CREATE INDEX IF NOT EXISTS idx_generated_queries_status ON generated_queries(status);
CREATE INDEX IF NOT EXISTS idx_businesses_status ON businesses(status);
CREATE INDEX IF NOT EXISTS idx_businesses_slug ON businesses(slug);
CREATE INDEX IF NOT EXISTS idx_final_output_status ON final_output(status);