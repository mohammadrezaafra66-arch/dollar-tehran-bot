"use client";
import { useEffect, useState } from "react";
import { api, type ExportItem } from "@/lib/api";

export default function DivarExportsPanel() {
  const [items, setItems] = useState<ExportItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  async function load() {
    setLoading(true);
    try { const res = await api.divar.exports(); setItems(res.items); }
    finally { setLoading(false); }
  }

  useEffect(() => { void load(); }, []);

  async function exportNow() {
    setLoading(true);
    try {
      const res = await api.divar.export();
      setMessage(`خروجی ساخته شد: ${res.file}`);
      await load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "خطا");
    } finally { setLoading(false); }
  }

  return (
    <div className="bg-white rounded-xl border p-5" dir="rtl">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-bold text-lg">خروجی‌های Excel دیوار</h2>
        <button onClick={() => void exportNow()} disabled={loading}
          className="bg-green-600 text-white rounded-lg px-4 py-2 text-sm disabled:opacity-50">
          {loading ? "در حال ساخت..." : "ساخت خروجی Excel"}
        </button>
      </div>
      {message && <div className="mb-3 p-3 bg-green-50 text-green-700 rounded-lg text-sm">{message}</div>}
      {items.length === 0
        ? <div className="text-center py-8 text-gray-400 text-sm">فایلی یافت نشد</div>
        : <div className="space-y-2">
            {items.map(item => (
              <div key={item.name} className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <div className="text-sm font-medium">{item.name}</div>
                  <div className="text-xs text-gray-400">{(item.size / 1024).toFixed(1)} KB — {item.modified}</div>
                </div>
                <a href={`/api/divar/exports/${item.name}`} download
                  className="text-blue-600 text-sm border border-blue-200 rounded-lg px-3 py-1">دانلود</a>
              </div>
            ))}
          </div>
      }
    </div>
  );
}
