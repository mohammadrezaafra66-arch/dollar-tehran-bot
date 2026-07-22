"use client";
import { useState, useEffect } from "react";
import { api } from "@/lib/api";

export default function TorobLogsViewer() {
  const [lines, setLines] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  async function load() {
    setLoading(true);
    try { const res = await api.torob.logs(150); setLines(res.lines); }
    finally { setLoading(false); }
  }

  useEffect(() => { void load(); }, []);

  return (
    <div className="bg-white rounded-xl border mb-6">
      <div className="flex items-center gap-3 p-4 border-b">
        <h2 className="font-bold flex-1">لاگ‌های ربات ترب</h2>
        <button onClick={load} disabled={loading} className="border rounded-lg px-3 py-1.5 text-sm">
          {loading ? "..." : "رفرش"}
        </button>
      </div>
      <pre className="bg-gray-950 text-green-400 text-xs p-4 rounded-b-xl overflow-auto max-h-80 font-mono leading-5">
        {lines.length === 0 ? "لاگی یافت نشد" : lines.join("\n")}
      </pre>
    </div>
  );
}
