# add_columns.py
import sqlite3
from app.config import Config

conn = sqlite3.connect(Config.DATABASE_PATH)
cursor = conn.cursor()

# اضافه کردن last_seen_at
try:
    cursor.execute('ALTER TABLE businesses ADD COLUMN last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    print('✅ last_seen_at column added')
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e):
        print('⚠️ last_seen_at already exists')
    else:
        print(f'⚠️ Error: {e}')

# اضافه کردن data_source
try:
    cursor.execute('ALTER TABLE businesses ADD COLUMN data_source TEXT DEFAULT "google_maps"')
    print('✅ data_source column added')
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e):
        print('⚠️ data_source already exists')
    else:
        print(f'⚠️ Error: {e}')

conn.commit()
conn.close()
print('✅ Done!')