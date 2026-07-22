"use client";
import { useState, useEffect } from "react";
import { api, DivarStats } from "@/lib/api";
import StatsBar from "@/components/divar/StatsBar";
import RunForm from "@/components/divar/RunForm";
import LeadsTable from "@/components/divar/LeadsTable";
import LogsViewer from "@/components/divar/LogsViewer";

type Tab = "leads" | "run" | "logs";

export default function DivarPage() {
  const [stats, setStats] = useState<DivarStats | null>(null);
  const [tab, setTab] = useState<Tab>("leads");

  useEffect(() => {
    api.divar.stats().then(setStats).catch(() => null);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 p-6" dir="rtl">
      <div className="max-w-6xl mx-auto">
        <header className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">پنل مدیریت ربات دیوار</h1>
          <p className="text-gray-500 text-sm mt-1">مشاهده، اجرا و مانیتورینگ ربات دیوار</p>
        </header>

        {stats && <StatsBar stats={stats} />}

        <nav className="flex gap-2 mb-6">
          {([["leads","لیدها"], ["run","اجرا"], ["logs","لاگ‌ها"]] as [Tab, string][]).map(([id, label]) => (
            <button key={id} onClick={() => setTab(id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                tab === id ? "bg-blue-600 text-white" : "bg-white border text-gray-600 hover:bg-gray-50"
              }`}>
              {label}
            </button>
          ))}
        </nav>

        {tab === "leads" && <LeadsTable />}
        {tab === "run" && <RunForm />}
        {tab === "logs" && <LogsViewer />}
      </div>
    </div>
  );
}
