"use client";
import { useState, useEffect } from "react";
import { api, type GoogleMapsStats } from "@/lib/api";
import GoogleMapsStatsBar from "@/components/google-maps/StatsBar";
import GoogleMapsConfigPanel from "@/components/google-maps/ConfigPanel";
import GoogleMapsRunForm from "@/components/google-maps/RunForm";
import GoogleMapsResultsTable from "@/components/google-maps/ResultsTable";
import GoogleMapsExportsPanel from "@/components/google-maps/ExportsPanel";
import GoogleMapsLogsViewer from "@/components/google-maps/LogsViewer";

type Tab = "config" | "run" | "results" | "exports" | "logs";
const TABS: [Tab, string][] = [
  ["config", "تنظیمات"],
  ["run", "اجرا"],
  ["results", "نتایج"],
  ["exports", "خروجی‌ها"],
  ["logs", "لاگ‌ها"],
];

export default function GoogleMapsPage() {
  const [stats, setStats] = useState<GoogleMapsStats | null>(null);
  const [tab, setTab] = useState<Tab>("results");

  useEffect(() => {
    api.googleMaps.stats().then(setStats).catch(() => null);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 p-6" dir="rtl">
      <div className="max-w-7xl mx-auto">
        <header className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">پنل مدیریت ربات گوگل مپ</h1>
          <p className="text-gray-500 text-sm mt-1">جستجو، استخراج و خروجی داده‌های گوگل مپ</p>
        </header>
        {stats && <GoogleMapsStatsBar stats={stats} />}
        <nav className="flex gap-2 mb-6 flex-wrap">
          {TABS.map(([id, label]) => (
            <button key={id} onClick={() => setTab(id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                tab === id ? "bg-blue-600 text-white" : "bg-white border text-gray-600 hover:bg-gray-50"
              }`}>{label}</button>
          ))}
        </nav>
        {tab === "config" && <GoogleMapsConfigPanel />}
        {tab === "run" && <GoogleMapsRunForm />}
        {tab === "results" && <GoogleMapsResultsTable />}
        {tab === "exports" && <GoogleMapsExportsPanel />}
        {tab === "logs" && <GoogleMapsLogsViewer />}
      </div>
    </div>
  );
}
