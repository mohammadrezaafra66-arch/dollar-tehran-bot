# debug_db.py
import sqlite3
from datetime import datetime, timedelta
from app.config import Config

# ========== تنظیمات ==========
PROCESSING_TIMEOUT_MINUTES = 10  # 10 دقیقه timeout برای processing
# =============================

def get_db_connection():
    """دریافت اتصال دیتابیس"""
    return sqlite3.connect(Config.DATABASE_PATH)

def ensure_schema():
    """اطمینان از وجود schema صحیح با updated_at NOT NULL"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # بررسی و اصلاح ستون updated_at
        cursor.execute("PRAGMA table_info(businesses)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'updated_at' not in columns:
            cursor.execute("ALTER TABLE businesses ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            print("✅ Added updated_at column")
        
        # به‌روزرسانی updated_at برای رکوردهای null
        cursor.execute("UPDATE businesses SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL")
        conn.commit()

def show_stats():
    """نمایش آمار سریع (--stats)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # آمار کلی
        cursor.execute("SELECT COUNT(*) FROM businesses")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT status, COUNT(*) FROM businesses GROUP BY status")
        statuses = {row[0]: row[1] for row in cursor.fetchall()}
        
        cursor.execute("SELECT COUNT(*) FROM businesses WHERE phone != '' AND phone IS NOT NULL")
        phones = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM businesses WHERE website != '' AND website IS NOT NULL")
        websites = cursor.fetchone()[0]
        
        print("=" * 40)
        print("📊 QUICK STATS")
        print("=" * 40)
        print(f"Total:     {total}")
        print(f"Done:      {statuses.get('done', 0)}")
        print(f"Failed:    {statuses.get('failed', 0)}")
        print(f"Pending:   {statuses.get('pending', 0)}")
        print(f"Processing:{statuses.get('processing', 0)}")
        print(f"Phones:    {phones}")
        print(f"Websites:  {websites}")
        print("=" * 40)

def show_full_status():
    """نمایش وضعیت کامل دیتابیس"""
    
    ensure_schema()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        print("=" * 60)
        print("📊 DATABASE HEALTH CHECK")
        print("=" * 60)
        print(f"Database: {Config.DATABASE_PATH}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Processing timeout: {PROCESSING_TIMEOUT_MINUTES} minutes")
        print("=" * 60)
        
        # 1. آمار کلی
        cursor.execute("SELECT COUNT(*) FROM businesses")
        total = cursor.fetchone()[0]
        print(f"\n📈 TOTAL BUSINESSES: {total}")
        
        # 2. وضعیت‌ها
        cursor.execute("SELECT status, COUNT(*) FROM businesses GROUP BY status")
        print("\n📊 STATUS BREAKDOWN:")
        for row in cursor.fetchall():
            print(f"   {row[0]}: {row[1]}")
        
        # 3. بیزینس‌های stuck در processing (با timeout)
        timeout_time = datetime.now() - timedelta(minutes=PROCESSING_TIMEOUT_MINUTES)
        cursor.execute("""
            SELECT COUNT(*) FROM businesses 
            WHERE status = 'processing' 
            AND datetime(updated_at) < datetime(?)
        """, (timeout_time.isoformat(),))
        stuck = cursor.fetchone()[0]
        
        if stuck > 0:
            print(f"\n⚠️ STUCK PROCESSING (> {PROCESSING_TIMEOUT_MINUTES} min): {stuck}")
            cursor.execute("""
                SELECT name, slug, updated_at FROM businesses 
                WHERE status = 'processing' 
                AND datetime(updated_at) < datetime(?)
                LIMIT 5
            """, (timeout_time.isoformat(),))
            for row in cursor.fetchall():
                print(f"   - {row[0]} (last: {row[2]})")
        
        # 4. بیزینس‌های failed
        cursor.execute("SELECT COUNT(*) FROM businesses WHERE status = 'failed'")
        failed = cursor.fetchone()[0]
        
        if failed > 0:
            print(f"\n❌ FAILED BUSINESSES: {failed}")
            cursor.execute("""
                SELECT name, retry_count, last_error, updated_at 
                FROM businesses WHERE status = 'failed' 
                LIMIT 5
            """)
            for row in cursor.fetchall():
                error_msg = row[2][:50] if row[2] else 'N/A'
                print(f"   - {row[0]} (retry: {row[1]}/3) - {error_msg}")
        
        # 5. کیفیت داده
        cursor.execute("SELECT COUNT(*) FROM businesses WHERE phone != '' AND phone IS NOT NULL")
        phones = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM businesses WHERE website != '' AND website IS NOT NULL")
        websites = cursor.fetchone()[0]
        
        print(f"\n📞 DATA QUALITY:")
        print(f"   Phone found: {phones} ({phones/total*100:.0f}%)" if total > 0 else "   Phone found: 0")
        print(f"   Website found: {websites} ({websites/total*100:.0f}%)" if total > 0 else "   Website found: 0")
        
        # 6. آخرین پردازش‌ها
        print(f"\n🕐 LAST 5 PROCESSED:")
        cursor.execute("""
            SELECT name, status, updated_at 
            FROM businesses 
            WHERE status IN ('done', 'failed')
            ORDER BY updated_at DESC 
            LIMIT 5
        """)
        for row in cursor.fetchall():
            print(f"   - {row[0][:35]} ... {row[1]} ({row[2]})")
        
        print("\n" + "=" * 60)
        print("✅ HEALTH CHECK COMPLETED")
        print("=" * 60)

def fix_stuck_processing():
    """رفع بیزینس‌های stuck در processing (فقط timeout شده‌ها)"""
    
    timeout_time = datetime.now() - timedelta(minutes=PROCESSING_TIMEOUT_MINUTES)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # فقط those که واقعاً stuck شده‌اند
        cursor.execute("""
            SELECT COUNT(*) FROM businesses 
            WHERE status = 'processing' 
            AND datetime(updated_at) < datetime(?)
        """, (timeout_time.isoformat(),))
        stuck_count = cursor.fetchone()[0]
        
        if stuck_count == 0:
            print("✅ No stuck processing jobs found")
            return 0
        
        print(f"🔧 Found {stuck_count} stuck processing jobs (older than {PROCESSING_TIMEOUT_MINUTES} minutes)")
        
        cursor.execute("""
            UPDATE businesses 
            SET status = 'pending', 
                last_error = 'Reset by admin (timeout)',
                updated_at = ?
            WHERE status = 'processing' 
            AND datetime(updated_at) < datetime(?)
        """, (datetime.now().isoformat(), timeout_time.isoformat()))
        
        conn.commit()
        count = cursor.rowcount
        
        print(f"✅ Reset {count} stuck processing jobs to pending")
        return count

def show_failed_details():
    """نمایش جزئیات کامل بیزینس‌های failed"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, retry_count, last_error, updated_at, slug
            FROM businesses 
            WHERE status = 'failed'
            ORDER BY updated_at DESC
        """)
        
        rows = cursor.fetchall()
        
        if not rows:
            print("✅ No failed businesses found")
            return
        
        print("\n❌ FAILED BUSINESSES DETAILS:")
        print("-" * 60)
        for row in rows:
            print(f"Name: {row[0]}")
            print(f"  Slug: {row[4]}")
            print(f"  Retry: {row[1]}/3")
            print(f"  Error: {row[2][:100] if row[2] else 'N/A'}")
            print(f"  Last attempt: {row[3]}")
            print("-" * 40)

def reset_all_processing():
    """reset همه processing‌ها (فقط در مواقع ضروری)"""
    print("⚠️ WARNING: This will reset ALL processing jobs, including active ones!")
    confirm = input("Are you sure? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("Cancelled")
        return 0
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE businesses 
            SET status = 'pending', 
                last_error = 'Reset by admin (force)',
                updated_at = ?
            WHERE status = 'processing'
        """, (datetime.now().isoformat(),))
        count = cursor.rowcount
        conn.commit()
        
        print(f"✅ Reset {count} processing jobs to pending")
        return count

def show_duplicates():
    """بررسی duplicateها بر اساس slug"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT slug, COUNT(*) as count 
            FROM businesses 
            GROUP BY slug 
            HAVING count > 1
        """)
        duplicates = cursor.fetchall()
        
        if duplicates:
            print("\n⚠️ DUPLICATES FOUND:")
            for row in duplicates:
                print(f"   {row[0]}: {row[1]} duplicates")
        else:
            print("\n✅ No duplicate slugs found")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--stats':
            show_stats()
        elif sys.argv[1] == '--fix':
            fix_stuck_processing()
        elif sys.argv[1] == '--failed':
            show_failed_details()
        elif sys.argv[1] == '--reset-all':
            reset_all_processing()
        elif sys.argv[1] == '--duplicates':
            show_duplicates()
        elif sys.argv[1] == '--schema':
            ensure_schema()
        else:
            print("""
Usage: python debug_db.py [OPTION]

Options:
    --stats         Quick statistics (done, failed, pending, processing, phones, websites)
    --fix           Fix only stuck processing jobs (older than timeout)
    --failed        Show detailed failed businesses
    --reset-all     Reset ALL processing jobs (use with caution!)
    --duplicates    Check for duplicate slugs
    --schema        Ensure schema is correct
    (no option)     Show full health check
""")
    else:
        show_full_status()