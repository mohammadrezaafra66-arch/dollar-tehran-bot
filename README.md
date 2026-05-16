# Dollar Tehran Price Bot

ربات مستقل قیمت دلار تهران برای اجرای روی کامپیوتر ویندوز.

این پروژه به دستیار افراکالا وابسته نیست. فقط اگر sync را فعال کنید، خروجی قیمت‌های جمع‌آوری‌شده را به جدول پویا در دستیار افراکالا می‌فرستد.

## خروجی اصلی

هر بار اجرا، این اطلاعات ذخیره می‌شود:

- source_name
- source_code
- buy_price_toman
- sell_price_toman
- average_price_toman
- raw_price_text
- source_url
- status
- error_message
- collected_at

داده‌ها در SQLite ذخیره می‌شوند:

```text
data/dollar_prices.db
```

## نصب سریع روی ویندوز

داخل پوشه پروژه:

```bat
copy config.example.yaml config.yaml
copy .env.example .env
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py run-once
```

یا ساده‌تر:

```bat
run_once.bat
```

برای داشبورد:

```bat
start_dashboard.bat
```

بعد برو به:

```text
http://127.0.0.1:8090
```

## تنظیم منابع

فایل `config.yaml` را باز کن. هر منبع داخل بخش `sources` تعریف می‌شود.

### حالت ۱: HTML + Regex

```yaml
- source_code: "source_1"
  source_name: "منبع نمونه"
  source_url: "https://example.com"
  enabled: true
  method: "html_regex"
  price_kind: "sell"
  regex: "([0-9]{2,3}(?:[,\\s][0-9]{3})+)"
```

### حالت ۲: HTML + CSS Selector

```yaml
- source_code: "source_2"
  source_name: "منبع selector"
  source_url: "https://example.com"
  enabled: true
  method: "html_selector"
  price_kind: "average"
  selector: ".usd-price"
```

### حالت ۳: JSON API

```yaml
- source_code: "source_api"
  source_name: "منبع API"
  source_url: "https://example.com/api/rates"
  enabled: true
  method: "json_path"
  price_kind: "average"
  json_path: "data.usd_tehran.price"
```

### حالت ۴: تست دستی

```yaml
- source_code: "manual_test"
  source_name: "تست دستی"
  source_url: "manual://test"
  enabled: true
  method: "manual"
  price_kind: "average"
  manual_price_toman: 68500
```

## اتصال به جدول پویا در افراکالا

در `.env` این موارد را تنظیم کن:

```env
AFRAKALA_API_BASE_URL=http://127.0.0.1:8000
AFRAKALA_BOT_API_KEY=CHANGE_ME
AFRAKALA_TABLE_SLUG=dollar-tehran-prices
```

بعد در `config.yaml`:

```yaml
sync:
  enabled: true
```

ربات اول با این endpoint جدول را از روی slug پیدا می‌کند:

```text
GET /api/public/bot/dynamic-tables/by-slug/{slug}
```

بعد هر ردیف قیمت را با این endpoint می‌فرستد:

```text
POST /api/public/bot/dynamic-tables/{table_id}/rows/upsert
```

بدنه ارسالی شامل `unique_key` است تا هر منبع و هر زمان جمع‌آوری، یک ردیف جدا داشته باشد.

## اجرای زمان‌بندی‌شده

برای اجرای دائمی:

```bat
run_loop.bat
```

فاصله اجرا از `config.yaml` تنظیم می‌شود:

```yaml
schedule:
  interval_minutes: 15
```

## خروجی Excel/CSV

```bat
python main.py export
```

فایل‌ها در پوشه `output` ساخته می‌شوند.

## نکته مهم

منابع نمونه واقعی نیستند و باید URL/selector/regex منابع واقعی خودت را در `config.yaml` وارد کنی. این کار عمدی است چون سایت‌ها ساختار ثابت ندارند و نباید کد را به یک سایت خاص قفل کنیم.
