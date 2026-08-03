# 🤖 G3 Bot Panel — مدیریت ربات‌های دیوار، ترب و گوگل مپ

## 📌 معرفی
این پنل یکپارچه برای مدیریت سه ربات استخراج لید طراحی شده است:
- **دیوار** — استخراج لید از آگهی‌های دیوار
- **ترب** — استخراج فروشندگان از ترب
- **گوگل مپ** — استخراج کسب‌وکارها از گوگل مپ

## 🚀 نصب و اجرا

### روش ۱ — با Docker (پیشنهادی)
```bash
# ۱. کلون کردن پروژه
git clone https://github.com/mohammadrezaafra66-arch/old-dollar-tehran-bot.git
cd old-dollar-tehran-bot

# ۲. کپی کردن فایل env
cp .env.example .env
# ویرایش .env با تنظیمات خود

# ۳. اجرا با docker-compose
docker-compose up -d

# ۴. باز کردن مرورگر
# فرانت: http://localhost:3010
# بک‌اند: http://localhost:8100
```

### روش ۲ — بدون Docker (ویندوز)
```bash
# ۱. دابل‌کلیک روی start.bat
# ۲. منتظر بمانید تا همه چیز نصب شود
# ۳. مرورگر به‌صورت خودکار باز می‌شود
```

### روش ۳ — اجرای دستی (توسعه)
```bash
# بک‌اند
cd panel-backend
python -m uvicorn app.main:app --reload --port 8100

# فرانت (در ترمینال جداگانه)
cd frontend
npm install
npm run dev
```

## 🔧 تنظیمات محیطی (.env)

| متغیر | توضیح | مثال |
|-------|-------|------|
| `AFRAKALA_API_URL` | آدرس API افراکالا برای سینک | `http://192.168.170.8:8000` |
| `CHROME_USER_DATA_DIR` | مسیر پروفایل Chrome | `C:\Users\...\Chrome\User Data` |
| `DB_PASSWORD` | رمز دیتابیس | `secure_password` |

## 📁 ساختار پروژه

```
old-dollar-tehran-bot/
├── panel-backend/          # بک‌اند یکپارچه FastAPI
│   └── app/
│       ├── main.py         # نقطه ورود
│       ├── routers/        # اندپوینت‌های API
│       └── services/       # مدیریت ربات‌ها
├── frontend/               # فرانت Next.js
│   └── app/
│       ├── divar/          # صفحه دیوار
│       ├── torob/          # صفحه ترب
│       ├── google-maps/    # صفحه گوگل مپ
│       └── help/           # صفحه راهنما
├── divar-bot/              # ربات دیوار
├── torob-bot/              # ربات ترب
├── google-maps-bot/        # ربات گوگل مپ
├── docker-compose.yml      # اجرا با Docker
├── start.bat               # اجرا در ویندوز
└── .env.example            # نمونه تنظیمات
```

## 🧪 تست

پس از اجرا، صفحه `/help` را باز کنید و راهنمای کامل را مطالعه کنید.

## ❓ مشکلات رایج

### ۱. خطای `CHROME_USER_DATA_DIR not set`
در فایل `.env` مسیر پروفایل Chrome را تنظیم کنید.

### ۲. خطای اتصال به دیتابیس
مطمئن شوید PostgreSQL در حال اجرا است و تنظیمات `.env` درست است.

### ۳. فرانت باز نمی‌شود
مطمئن شوید پورت ۳۰۱۰ در فایروال باز است و بک‌اند در حال اجرا است.

## 📞 پشتیبانی
برای سوالات و مشکلات، با تیم پشتیبانی تماس بگیرید.
