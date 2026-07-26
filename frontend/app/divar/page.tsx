"use client";
import { useState, useEffect } from "react";
import { api, type DivarStats } from "@/lib/api";
import StatsBar from "@/components/divar/StatsBar";
import SessionPanel from "@/components/divar/SessionPanel";
import ConfigPanel from "@/components/divar/ConfigPanel";
import RunForm from "@/components/divar/RunForm";
import LeadsTable from "@/components/divar/LeadsTable";
import AIPanel from "@/components/divar/AIPanel";
import DivarExportsPanel from "@/components/divar/ExportsPanel";
import LogsViewer from "@/components/divar/LogsViewer";

type Tab = "accounts"|"config"|"run"|"leads"|"ai"|"exports"|"logs";
const TABS: [Tab, string][] = [
  ["accounts","اکانت‌ها"],["config","تنظیمات"],["run","اجرا"],
  ["leads","لیدها"],["ai","AI"],["exports","خروجی‌ها"],["logs","لاگ‌ها"],
];

export default function DivarPage() {
  const [stats, setStats] = useState<DivarStats | null>(null);
  const [tab, setTab] = useState<Tab>("accounts");

  useEffect(() => {
    api.divar.stats().then(setStats).catch(() => null);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 p-6" dir="rtl">
      <div className="max-w-7xl mx-auto">
        <header className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">پنل مدیریت ربات دیوار</h1>
          <p className="text-gray-500 text-sm mt-1">مدیریت کامل اکانت‌ها، اجرا و مانیتورینگ</p>
        </header>
        {stats && <StatsBar stats={stats} />}
        <nav className="flex gap-2 mb-6 flex-wrap">
          {TABS.map(([id, label]) => (
            <button key={id} onClick={() => setTab(id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                tab === id ? "bg-blue-600 text-white" : "bg-white border text-gray-600 hover:bg-gray-50"
              }`}>{label}</button>
          ))}
        </nav>
        {tab === "accounts" && <SessionPanel />}
        {tab === "config"   && <ConfigPanel />}
        {tab === "run"      && <RunForm />}
        {tab === "leads"    && <LeadsTable />}
        {tab === "ai"       && <AIPanel />}
        {tab === "exports"  && <DivarExportsPanel />}
        {tab === "logs"     && <LogsViewer />}
      </div>
    </div>
  );
}
