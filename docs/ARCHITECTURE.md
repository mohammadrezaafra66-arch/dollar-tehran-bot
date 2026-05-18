# معماری صنعتی Afra Market Data Platform

## هدف نهایی

هدف پروژه فقط استخراج قیمت دلار تهران نیست. هدف، ساخت یک پلتفرم داده بازار برای افرا کالا است که بتواند:

- حداقل ۵۰ شاخص مختلف را مدیریت کند.
- برای هر شاخص حداقل ۵ منبع یا کانال داشته باشد.
- در مجموع حدود ۲۵۰ منبع را پایش کند.
- داده خام، داده نرمال‌شده، وضعیت منبع، تاریخچه تغییرات، میانگین‌ها، فیلترها و شاخص‌های تصمیم‌گیری را ذخیره کند.
- خروجی قابل‌مصرف برای داشبورد داخلی و API وب‌اپلیکیشن دستیار هوشمند افرا کالا تولید کند.
- در آینده امکان تحلیل، هشدار، پیش‌بینی، قیمت‌گذاری و کمک به تیم حسابداری را فراهم کند.

## اصل مهم طراحی

این پروژه نباید به شکل مجموعه‌ای از اسکریپرهای پراکنده رشد کند. هر شاخص، منبع، فرمول، خروجی و API باید قرارداد مشخص داشته باشد.

معماری درست:

```text
Source Registry
   ↓
Collector / Fetcher
   ↓
Extractor
   ↓
Normalizer
   ↓
Validator / Quality Engine
   ↓
Raw SQL Storage + Normalized SQL Storage
   ↓
Aggregation Engine
   ↓
Derived Indicator Engine
   ↓
Dashboard + API Export Layer
   ↓
Afra Kala Assistant Web Application
```

## لایه‌ها

### 1. Source Registry

تمام منابع باید در کانفیگ یا دیتابیس تعریف شوند. هیچ منبعی نباید در کد hard-code شود.

هر source باید این فیلدها را داشته باشد:

- `source_code`
- `source_name`
- `indicator_code`
- `url` یا مشخصات کانال
- `source_type`: `html`, `json_api`, `telegram`, `manual`, `file`, `browser`
- `price_kind`: `current`, `buy`, `sell`, `average`
- `unit`: `rial`, `toman`, `usd`, ...
- `fetch_interval_seconds`
- `timeout_seconds`
- `enabled`
- `priority`
- `trust_score`
- `extractor_steps`

### 2. Collector / Fetcher

وظیفه fetcher فقط گرفتن محتوا است، نه تحلیل قیمت.

Fetcher باید بتواند انواع ورودی را پشتیبانی کند:

- HTML ساده با requests
- صفحه JavaScript با browser worker در صورت نیاز
- JSON API
- Telegram channel در آینده
- فایل یا ورودی دستی

### 3. Extractor

Extractor فقط مقدار خام را از محتوای منبع بیرون می‌کشد.

روش‌های مجاز:

- CSS selector
- XPath در آینده
- Regex
- JSONPath
- row_contains
- custom parser فقط در موارد اضطراری

قانون: اول روش پایدارتر، بعد selector شکننده.

### 4. Normalizer

Normalizer همه داده‌ها را به قالب استاندارد تبدیل می‌کند:

- تبدیل ارقام فارسی، عربی، انگلیسی به عدد استاندارد
- حذف کاما و فاصله
- تبدیل ریال به تومان
- ثبت واحد ورودی و واحد خروجی
- تبدیل زمان به ساعت ایران
- ذخیره تاریخ شمسی و میلادی

خروجی استاندارد هر observation:

```json
{
  "indicator_code": "usd_tehran",
  "source_code": "tgju_usd_tehran_current",
  "price_kind": "current",
  "value": 179920,
  "unit": "toman",
  "raw_value": "1,799,200",
  "observed_at_iran": "17:35:20",
  "observed_at_jalali": "1405/02/28",
  "status": "ok"
}
```

### 5. Validator / Quality Engine

هر عددی که استخراج شد نباید مستقیم وارد شاخص تصمیم‌گیری شود.

باید بررسی شود:

- آیا عدد خالی است؟
- آیا نسبت به آخرین مقدار جهش غیرعادی دارد؟
- آیا منبع در window زمانی معتبر آپدیت شده؟
- آیا مقدار با سایر منابع فاصله شدید دارد؟
- آیا منبع چند بار پشت سر هم خطا داده؟

وضعیت‌های پیشنهادی:

- `ok`
- `stale`
- `outlier`
- `parse_error`
- `fetch_error`
- `disabled`
- `low_confidence`

### 6. SQL Storage

برای MVP می‌توان SQLite داشت، اما برای تولید واقعی با ۲۵۰ منبع لحظه‌ای، SQLite کافی نیست.

استاندارد پیشنهادی تولید:

- PostgreSQL برای ساختار اصلی
- TimescaleDB برای time-series در صورت رشد زیاد
- Redis برای cache لحظه‌ای داشبورد، در فاز بعدی

قانون مهم: داده خام و داده نرمال‌شده جدا ذخیره شوند.

### 7. Aggregation Engine

این لایه شاخص‌های پایه را از چند source می‌سازد.

مثال برای دلار تهران:

- آخرین مقدار معتبر هر source
- میانگین ساده
- median
- weighted average بر اساس trust_score
- حذف outlierها
- فیلتر زمان: فقط منابع آپدیت‌شده در ۱۵ دقیقه اخیر
- فیلتر تغییر: فقط منابعی که نسبت به ۲۰ دقیقه قبل تغییر کرده‌اند

نمونه query منطقی:

```text
برای usd_tehran:
  منابع ok
  در ۱۵ دقیقه اخیر
  با اختلاف نسبت به ۲۰ دقیقه قبل
  حذف outlier
  محاسبه median و weighted_average
```

### 8. Derived Indicator Engine

شاخص‌های تصمیم‌گیری از شاخص‌های پایه ساخته می‌شوند.

مثال:

```text
usd_tehran_decision_index =
  weighted_avg(usd_tehran valid sources last 15m)
  + trend_factor(last 20m)
  + volatility_factor(last 60m)
  - stale_penalty
```

پارامترها باید قابل تنظیم باشند:

- `freshness_window_minutes`
- `comparison_window_minutes`
- `min_sources`
- `outlier_threshold_percent`
- `weights`
- `trend_weight`
- `volatility_weight`

هیچ فرمولی نباید در داشبورد hard-code شود؛ باید در config یا جدول rules ذخیره شود.

### 9. Dashboard

داشبورد باید چند سطح داشته باشد:

- وضعیت لحظه‌ای منابع
- وضعیت شاخص‌ها
- مقایسه منابع یک شاخص
- خطاهای fetch/parse
- داده‌های stale
- outlierها
- نمودار تاریخچه
- خروجی‌های آماده API
- شاخص‌های تصمیم‌گیری

### 10. API Export Layer

وب‌اپلیکیشن افرا کالا نباید به دیتابیس استخراج مستقیم وصل شود. ارتباط باید از طریق API قرارداددار باشد.

Endpointهای پیشنهادی:

```text
GET /api/indicators
GET /api/indicators/{code}/latest
GET /api/indicators/{code}/history?from=&to=&source=
GET /api/indicators/{code}/sources
GET /api/derived/{code}/latest
POST /api/export/afra-kala
```

## استانداردهای اجباری توسعه

1. هر source باید مستقل خراب شود؛ خرابی یک source نباید کل ربات را بخواباند.
2. هر عدد باید raw و normalized ذخیره شود.
3. همه خروجی‌های مالی باید unit مشخص داشته باشند.
4. همه زمان‌ها باید هم UTC، هم Iran time، هم Jalali date داشته باشند.
5. هر شاخص باید حداقل یک source معتبر داشته باشد، ولی برای شاخص تصمیم‌گیری حداقل منابع قابل تنظیم است.
6. داشبورد فقط مصرف‌کننده داده باشد، نه محل منطق اصلی.
7. فرمول‌های تصمیم‌گیری باید نسخه‌بندی شوند.
8. تغییرات schema باید migration داشته باشد.
9. خروجی API باید backward-compatible باشد.
10. هر منبع باید health و consecutive_failures داشته باشد.

## فازبندی پیشنهادی

### فاز 1: Foundation

- کانفیگ استاندارد شاخص‌ها و منابع
- storage استاندارد
- dashboard پایه
- API payload
- health check منابع

### فاز 2: Production Storage

- مهاجرت از SQLite به PostgreSQL
- جدول‌بندی حرفه‌ای
- migration
- indexهای زمانی

### فاز 3: Aggregation

- median
- weighted average
- outlier detection
- freshness window
- comparison window

### فاز 4: Derived Indicators

- rule engine
- شاخص تصمیم‌گیری دلار تهران
- فرمول‌های قابل تنظیم
- backtest ساده روی تاریخچه

### فاز 5: API Integration

- endpointهای خروجی
- token auth
- retry queue
- export log

### فاز 6: Monitoring

- source health dashboard
- alert
- error budget
- stale source detection

## تصمیم معماری مهم

نسخه فعلی می‌تواند برای توسعه و تست محلی با SQLite ادامه پیدا کند، اما اگر واقعاً ۲۵۰ منبع با آپدیت لحظه‌ای می‌خواهیم، باید از همین ابتدا schema و naming را طوری بنویسیم که بعداً بدون بازنویسی منطق، به PostgreSQL منتقل شود.
