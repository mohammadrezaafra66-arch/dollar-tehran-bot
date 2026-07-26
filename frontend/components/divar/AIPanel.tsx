"use client";
import { useEffect, useState } from "react";
import { api, type DivarAIStats } from "@/lib/api";

export default function AIPanel() {
  const [stats, setStats] = useState<DivarAIStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  async function load() {
    setLoading(true);
    try { setStats(await api.divar.aiStats()); }
    finally { setLoading(false); }
  }

  useEffect(() => { void load(); }, []);

  async function runAI() {
    setLoading(true);
    try {
      await api.divar.aiRun();
      setMessage("تحلیل AI شروع شد.");
      await load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "خطا");
    } finally { setLoading(false); }
  }

  return (
    <div className="bg-white rounded-xl border p-5 mb-6" dir="rtl">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="font-bold text-lg">تحلیل AI دیوار</h2>
          <p className="text-sm text-gray-500">پردازش خودکار متن و تحلیل لیدها</p>
        </div>
        <button onClick={() => void runAI()} disabled={loading}
          className="bg-purple-600 text-white rounded-lg px-4 py-2 text-sm disabled:opacity-50">
          {loading ? "در حال اجرا..." : "اجرای تحلیل AI"}
        </button>
      </div>
      {message && <div className="mb-4 rounded-lg border border-purple-200 bg-purple-50 p-3 text-sm text-purple-700">{message}</div>}
      {stats && (
        <div className="grid gap-4 md:grid-cols-4">
          <div className="rounded-lg border p-3 text-center"><div className="text-2xl font-bold">{stats.total}</div><div className="text-xs text-gray-500 mt-1">کل لیدها</div></div>
          <div className="rounded-lg border p-3 text-center"><div className="text-2xl font-bold text-green-600">{stats.analyzed}</div><div className="text-xs text-gray-500 mt-1">تحلیل‌شده</div></div>
          <div className="rounded-lg border p-3 text-center"><div className="text-2xl font-bold text-yellow-600">{stats.pending}</div><div className="text-xs text-gray-500 mt-1">در انتظار</div></div>
          <div className="rounded-lg border p-3 text-center"><div className="text-2xl font-bold text-red-600">{stats.failed}</div><div className="text-xs text-gray-500 mt-1">ناموفق</div></div>
        </div>
      )}
    </div>
  );
}
