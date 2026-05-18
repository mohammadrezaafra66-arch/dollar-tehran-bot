-- Afra Market Data Platform - Industrial SQL Schema Vision
-- هدف: طراحی قابل ارتقا از SQLite به PostgreSQL/TimescaleDB

-- 1) شاخص‌ها
CREATE TABLE IF NOT EXISTS indicators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category TEXT,
    base_unit TEXT NOT NULL DEFAULT 'toman',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 2) منابع هر شاخص
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    indicator_code TEXT NOT NULL,
    name TEXT NOT NULL,
    source_type TEXT NOT NULL DEFAULT 'html',
    url TEXT,
    price_kind TEXT NOT NULL DEFAULT 'current',
    input_unit TEXT NOT NULL,
    output_unit TEXT NOT NULL DEFAULT 'toman',
    fetch_interval_seconds INTEGER NOT NULL DEFAULT 180,
    timeout_seconds INTEGER NOT NULL DEFAULT 20,
    priority INTEGER NOT NULL DEFAULT 100,
    trust_score REAL NOT NULL DEFAULT 1.0,
    enabled INTEGER NOT NULL DEFAULT 1,
    extractor_config_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(indicator_code) REFERENCES indicators(code)
);

-- 3) هر اجرای fetch از یک منبع
CREATE TABLE IF NOT EXISTS source_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_code TEXT NOT NULL,
    indicator_code TEXT NOT NULL,
    started_at_utc TEXT NOT NULL,
    finished_at_utc TEXT,
    started_at_iran TEXT,
    started_at_jalali TEXT,
    status TEXT NOT NULL,
    http_status INTEGER,
    duration_ms INTEGER,
    error_type TEXT,
    error_message TEXT,
    raw_content_hash TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(source_code) REFERENCES sources(code),
    FOREIGN KEY(indicator_code) REFERENCES indicators(code)
);

-- 4) داده خام استخراج‌شده
CREATE TABLE IF NOT EXISTS raw_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    indicator_code TEXT NOT NULL,
    source_code TEXT NOT NULL,
    price_kind TEXT NOT NULL,
    raw_value TEXT,
    raw_unit TEXT,
    raw_context TEXT,
    observed_at_utc TEXT NOT NULL,
    observed_at_iran TEXT,
    observed_at_jalali TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES source_runs(id)
);

-- 5) داده نرمال‌شده قابل استفاده
CREATE TABLE IF NOT EXISTS normalized_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_observation_id INTEGER,
    indicator_code TEXT NOT NULL,
    source_code TEXT NOT NULL,
    price_kind TEXT NOT NULL,
    value REAL NOT NULL,
    unit TEXT NOT NULL DEFAULT 'toman',
    quality_status TEXT NOT NULL DEFAULT 'ok',
    quality_score REAL NOT NULL DEFAULT 1.0,
    is_outlier INTEGER NOT NULL DEFAULT 0,
    is_stale INTEGER NOT NULL DEFAULT 0,
    observed_at_utc TEXT NOT NULL,
    observed_at_iran TEXT,
    observed_at_jalali TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(raw_observation_id) REFERENCES raw_observations(id)
);

-- 6) snapshot تجمیع‌شده شاخص‌ها
CREATE TABLE IF NOT EXISTS indicator_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    indicator_code TEXT NOT NULL,
    value_median REAL,
    value_average REAL,
    value_weighted_average REAL,
    value_min REAL,
    value_max REAL,
    source_count INTEGER NOT NULL,
    valid_source_count INTEGER NOT NULL,
    stale_source_count INTEGER NOT NULL DEFAULT 0,
    outlier_source_count INTEGER NOT NULL DEFAULT 0,
    freshness_window_minutes INTEGER NOT NULL,
    calculation_config_json TEXT,
    calculated_at_utc TEXT NOT NULL,
    calculated_at_iran TEXT,
    calculated_at_jalali TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(indicator_code) REFERENCES indicators(code)
);

-- 7) فرمول‌ها و شاخص‌های مشتق‌شده
CREATE TABLE IF NOT EXISTS derived_indicators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    formula_version TEXT NOT NULL,
    formula_json TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 8) خروجی شاخص‌های مشتق‌شده
CREATE TABLE IF NOT EXISTS derived_indicator_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    derived_code TEXT NOT NULL,
    value REAL,
    unit TEXT,
    confidence_score REAL,
    input_snapshot_ids_json TEXT,
    formula_version TEXT NOT NULL,
    calculated_at_utc TEXT NOT NULL,
    calculated_at_iran TEXT,
    calculated_at_jalali TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(derived_code) REFERENCES derived_indicators(code)
);

-- 9) وضعیت سلامت منابع
CREATE TABLE IF NOT EXISTS source_health (
    source_code TEXT PRIMARY KEY,
    indicator_code TEXT NOT NULL,
    last_ok_at_utc TEXT,
    last_error_at_utc TEXT,
    consecutive_failures INTEGER NOT NULL DEFAULT 0,
    last_error_type TEXT,
    last_error_message TEXT,
    health_status TEXT NOT NULL DEFAULT 'unknown',
    updated_at TEXT NOT NULL,
    FOREIGN KEY(source_code) REFERENCES sources(code)
);

-- 10) لاگ ارسال به API افرا کالا
CREATE TABLE IF NOT EXISTS api_export_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target TEXT NOT NULL,
    payload_hash TEXT,
    status TEXT NOT NULL,
    http_status INTEGER,
    response_text TEXT,
    error_message TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_normalized_indicator_time ON normalized_observations(indicator_code, observed_at_utc);
CREATE INDEX IF NOT EXISTS idx_normalized_source_time ON normalized_observations(source_code, observed_at_utc);
CREATE INDEX IF NOT EXISTS idx_snapshots_indicator_time ON indicator_snapshots(indicator_code, calculated_at_utc);
CREATE INDEX IF NOT EXISTS idx_source_runs_status_time ON source_runs(status, started_at_utc);
