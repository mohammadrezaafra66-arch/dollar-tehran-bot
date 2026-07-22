"use client";
import { useState, useEffect } from "react";
import { api, TorobStats } from "@/lib/api";
import TorobStatsBar from "@/components/torob/StatsBar";
import TorobRunForm from "@/components/torob/RunForm";
import SellersTable from "@/components/torob/SellersTable";
import ReportsTable from "@/components/torob/ReportsTable";
import TorobLogsViewer from "@/components/torob/LogsViewer";

type Tab = "sellers" | "reports" | "run" | "logs";

export default function TorobPage() {
  const [stats, setStats] = useState<TorobStats | null>(null);
  const [tab, setTab] = useState<Tab>("sellers");

  useEffect(() => {
    api.torob.stats().then(setStats).catch(() => null);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 p-6" dir="rtl">
      <div className="max-w-6xl mx-auto">
        <header className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">پنل مدیریت ربات ترب</h1>
          <p className="text-gray-500 text-sm mt-1">جستجو، فروشندگان و گزارش قیمت</p>
        </header>

        {stats && <TorobStatsBar stats={stats} />}

        <nav className="flex gap-2 mb-6">
          {([["sellers","فروشندگان"],["reports","گزارش قیمت"],["run","اجرا"],["logs","لاگ‌ها"]] as [Tab,string][]).map(([id,label]) => (
            <button key={id} onClick={() => setTab(id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                tab === id ? "bg-blue-600 text-white" : "bg-white border text-gray-600 hover:bg-gray-50"
              }`}>
              {label}
            </button>
          ))}
        </nav>

        {tab === "sellers"  && <SellersTable />}
        {tab === "reports"  && <ReportsTable />}
        {tab === "run"      && <TorobRunForm />}
        {tab === "logs"     && <TorobLogsViewer />}
      </div>
    </div>
  );
}
