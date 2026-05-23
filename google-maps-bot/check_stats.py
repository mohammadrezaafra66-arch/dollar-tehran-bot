# check_stats.py
from app.database import Database

db = Database()
with db._get_connection() as conn:
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM businesses')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM businesses WHERE status = "done"')
    done = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM businesses WHERE data_source = "google_maps"')
    data_source = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM businesses WHERE last_seen_at IS NOT NULL')
    last_seen = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM businesses WHERE phone != "" AND phone IS NOT NULL')
    phones = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM businesses WHERE website != "" AND website IS NOT NULL')
    websites = cursor.fetchone()[0]
    
    print('=' * 50)
    print('📊 Current Database Stats')
    print('=' * 50)
    print(f'Total businesses: {total}')
    print(f'Done: {done}')
    print(f'With data_source: {data_source}')
    print(f'With last_seen_at: {last_seen}')
    print(f'With phone: {phones}')
    print(f'With website: {websites}')
    
    # نمونه بیزینس‌ها
    cursor.execute('SELECT name, phone, website, data_source, last_seen_at FROM businesses LIMIT 5')
    print('\n📋 Sample businesses:')
    for row in cursor.fetchall():
        name = row[0][:35] if row[0] else 'N/A'
        phone = row[1][:15] if row[1] else 'N/A'
        print(f'  - {name} | phone: {phone} | source: {row[3]}')

db.close()