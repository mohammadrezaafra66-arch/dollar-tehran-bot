import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path


def export_to_excel(db_path: str, output_dir: str = "output") -> str:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("""
        SELECT
            title AS 'عنوان',
            seller_name AS 'نام فروشنده',
            phone AS 'شماره تلفن',
            city AS 'شهر',
            district AS 'منطقه',
            price_text AS 'قیمت',
            description AS 'توضیحات',
            ai_analysis AS 'تحلیل AI',
            message_status AS 'وضعیت پیام',
            message_sent_at AS 'زمان ارسال پیام',
            source_url AS 'لینک آگهی',
            published_at AS 'تاریخ انتشار',
            created_at AS 'تاریخ استخراج'
        FROM divar_leads
        ORDER BY id DESC
    """, conn)
    conn.close()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_path = f"{output_dir}/divar_leads_{timestamp}.xlsx"
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="لیدها", index=False)
    print(f"Excel ذخیره شد: {output_path}")
    return output_path
