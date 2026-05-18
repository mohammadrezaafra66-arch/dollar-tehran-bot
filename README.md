# Afra Market Data Bot

ربات ماژولار استخراج شاخص‌های بازار برای انتقال به داشبورد و API دستیار هوشمند افرا کالا.

این نسخه جایگزین ساختار قبلی `dollar_bot` شده و برای رشد تا ۵۰+ شاخص طراحی شده است. اضافه‌کردن سایت یا شاخص جدید باید از طریق کانفیگ انجام شود، نه با ساخت اسکریپرهای پراکنده.

## اجرای سریع در ویندوز

برای اجرای یک‌باره:

```bat
run_once.bat
```

برای اجرای دائمی هر ۳ دقیقه:

```bat
run_loop.bat
```

برای داشبورد:

```bat
start_dashboard.bat
```

آدرس داشبورد:

```text
http://127.0.0.1:8090
```

برای اجرای همزمان داشبورد و ربات:

```bat
start_all.bat
```

## ساختار پروژه

```text
afra_market_data/
  core.py          موتور استخراج، نرمال‌سازی، ذخیره‌سازی، تاریخ شمسی، ارسال API
  cli.py           دستورهای run-once / run-loop / post
  dashboard.py     داشبورد FastAPI با دکمه اجرای فوری
configs/
  indicators.json  تعریف شاخص‌ها و سایت‌ها
main.py            نقطه ورود CLI
dashboard.py       نقطه ورود داشبورد
```

## شاخص‌ها و منابع فعلی

در فایل `configs/indicators.json` این موارد منتقل شده‌اند:

- TGJU - دلار تهران
- TGJU - درهم امارات
- TGJU - یورو
- signal - دلار تهران
- alanchand - دلار تهران خرید
- alanchand - دلار تهران فروش
- Bonbast - دلار تهران فروش/current
- Bonbast - دلار تهران خرید
- Tabdeal - دلار تهران

همه خروجی‌ها در نهایت به تومان نرمال می‌شوند. اگر منبع ریال بدهد، تقسیم بر ۱۰ می‌شود؛ اگر منبع تومان بدهد، بدون تبدیل ذخیره می‌شود.

## خروجی‌ها

دیتابیس محلی:

```text
data/market_data.db
```

آخرین payload آماده API:

```text
output/latest_payload.json
```

## اتصال به API افرا کالا

در `.env` یا متغیر محیطی ویندوز تنظیم کن:

```env
AFRA_API_URL=https://example.com/api/market-data/bulk
AFRA_API_TOKEN=YOUR_TOKEN
```

بعد در `configs/indicators.json` مقدار زیر را فعال کن:

```json
"sync": {"enabled": true}
```

و اجرا کن:

```bat
python main.py post
```

## اضافه‌کردن سایت جدید

داخل `configs/indicators.json`، به شاخص مربوطه یک source اضافه کن:

```json
{
  "code": "source_code",
  "name": "نام سایت - نام شاخص",
  "url": "https://example.com",
  "enabled": true,
  "price_kind": "current",
  "unit": "rial",
  "extractors": [
    {"kind": "css", "selector": ".price"},
    {"kind": "regex", "pattern": "([0-9,]+)"}
  ]
}
```

انواع extractor فعلی:

- `css`: استخراج با CSS selector
- `regex`: استخراج با regex از HTML
- `row_contains`: پیدا کردن ردیف/بلوک بر اساس کلمات و سپس عدد داخل همان بلوک

## استانداردهای اجباری پروژه

- هیچ شاخصی نباید مستقیم داخل کد hard-code شود.
- هر منبع باید `code` یکتا داشته باشد.
- واحد ورودی هر منبع باید دقیق مشخص شود: `rial` یا `toman`.
- همه زمان‌ها در داشبورد به ساعت ایران و تاریخ شمسی نمایش داده می‌شوند.
- خروجی API همیشه تومان است.
- اگر منبع خراب شد، نباید کل ربات بخوابد؛ فقط همان source خطا می‌گیرد.
