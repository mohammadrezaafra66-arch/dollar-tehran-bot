export default function HelpPage() {
  return (
    <div className="min-h-screen bg-gray-50 p-6" dir="rtl">
      <div className="max-w-4xl mx-auto bg-white rounded-2xl border p-6">
        <h1 className="text-2xl font-bold mb-4">راهنمای پنل افراکالا</h1>
        <ul className="space-y-3 text-sm text-gray-700">
          <li>1. از داشبورد، ربات موردنظر را انتخاب کنید.</li>
          <li>2. در تب اجرا، کوئری یا URL را وارد کنید.</li>
          <li>3. خروجی‌ها در تب خروجی‌ها قابل مشاهده‌اند.</li>
          <li>4. لاگ‌ها از تب لاگ‌ها قابل بررسی هستند.</li>
        </ul>
      </div>
    </div>
  );
}
