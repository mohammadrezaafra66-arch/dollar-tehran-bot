"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api, type DivarStats, type TorobStats, type GoogleMapsStats } from "@/lib/api";

export default function Dashboard() {
  const [divar, setDivar] = useState<DivarStats | null>(null);
  const [torob, setTorob] = useState<TorobStats | null>(null);
  const [googleMaps, setGoogleMaps] = useState<GoogleMapsStats | null>(null);
  const [health, setHealth] = useState<string>("...");

  useEffect(() => {
    api.health().then(r => setHealth(r.status)).catch(() => setHealth("خطا"));
    api.divar.stats().then(setDivar).catch(() => null);
    api.torob.stats().then(setTorob).catch(() => null);
    api.googleMaps.stats().then(setGoogleMaps).catch(() => null);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 p-6" dir="rtl">
      <div className="max-w-5xl mx-auto">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">داشبورد افراکالا</h1>
          <p className="text-gray-500 mt-1">کنترل پنل ربات‌های دیوار و ترب</p>
          <span className={`inline-flex items-center gap-1.5 mt-2 text-xs px-3 py-1 rounded-full ${health === "ok" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${health === "ok" ? "bg-green-500" : "bg-red-500"}`} />
            بک‌اند: {health}
          </span>
        </header>

        <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-2xl border p-6">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="font-bold text-lg">ربات دیوار</h2>
                <p className="text-gray-500 text-sm">استخراج لید و ارسال پیام</p>
              </div>
              <Link href="/divar" className="bg-blue-600 text-white rounded-lg px-4 py-2 text-sm">مدیریت</Link>
            </div>
            {divar ? (
              <div className="grid grid-cols-3 gap-3">
                <div className="text-center p-2 bg-gray-50 rounded-lg"><div className="font-bold text-xl">{divar.total_leads}</div><div className="text-xs text-gray-500">کل لید</div></div>
                <div className="text-center p-2 bg-green-50 rounded-lg"><div className="font-bold text-xl text-green-600">{divar.messages_sent}</div><div className="text-xs text-gray-500">پیام ارسالی</div></div>
                <div className="text-center p-2 bg-yellow-50 rounded-lg"><div className="font-bold text-xl text-yellow-600">{divar.pending}</div><div className="text-xs text-gray-500">در انتظار</div></div>
              </div>
            ) : <div className="text-center py-4 text-gray-400 text-sm">در حال بارگذاری...</div>}
          </div>

          <div className="bg-white rounded-2xl border p-6">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="font-bold text-lg">ربات ترب</h2>
                <p className="text-gray-500 text-sm">جستجو و گزارش قیمت</p>
              </div>
              <Link href="/torob" className="bg-blue-600 text-white rounded-lg px-4 py-2 text-sm">مدیریت</Link>
            </div>
            {torob ? (
              <div className="grid grid-cols-3 gap-3">
                <div className="text-center p-2 bg-gray-50 rounded-lg"><div className="font-bold text-xl">{torob.total_sellers}</div><div className="text-xs text-gray-500">فروشنده</div></div>
                <div className="text-center p-2 bg-blue-50 rounded-lg"><div className="font-bold text-xl text-blue-600">{torob.total_reports}</div><div className="text-xs text-gray-500">گزارش</div></div>
                <div className="text-center p-2 bg-purple-50 rounded-lg"><div className="font-bold text-xl text-purple-600">{torob.total_history}</div><div className="text-xs text-gray-500">تاریخچه</div></div>
              </div>
            ) : <div className="text-center py-4 text-gray-400 text-sm">در حال بارگذاری...</div>}
          </div>

          <div className="bg-white rounded-2xl border p-6">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="font-bold text-lg">ربات گوگل مپ</h2>
                <p className="text-gray-500 text-sm">استخراج کسب‌وکارها و خروجی اکسل</p>
              </div>
              <Link href="/google-maps" className="bg-blue-600 text-white rounded-lg px-4 py-2 text-sm">مدیریت</Link>
            </div>
            {googleMaps ? (
              <div className="grid grid-cols-3 gap-3">
                <div className="text-center p-2 bg-gray-50 rounded-lg"><div className="font-bold text-xl">{googleMaps.total_records}</div><div className="text-xs text-gray-500">کل رکورد</div></div>
                <div className="text-center p-2 bg-green-50 rounded-lg"><div className="font-bold text-xl text-green-600">{googleMaps.synced}</div><div className="text-xs text-gray-500">ثبت‌شده</div></div>
                <div className="text-center p-2 bg-yellow-50 rounded-lg"><div className="font-bold text-xl text-yellow-600">{googleMaps.pending}</div><div className="text-xs text-gray-500">در انتظار</div></div>
              </div>
            ) : <div className="text-center py-4 text-gray-400 text-sm">در حال بارگذاری...</div>}
          </div>
        </div>
      </div>
    </div>
  );
}
