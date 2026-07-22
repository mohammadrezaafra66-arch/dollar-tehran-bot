"use client";
import { useCallback, useEffect, useState } from "react";
import { api, DivarSendLog } from "@/lib/api";

const STATUS_COLORS: Record<string, string> = {
  sent: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
};

function truncateText(value: string, max = 60) {
  if (!value) return "—";
  return value.length > max ? `${value.slice(0, max)}…` : value;
}

export default function SendLogTable() {
  const [items, setItems] = useState<DivarSendLog[]>([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.divar.sendLog(100);
      setItems(res.items);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="bg-white rounded-xl border mb-6">
      <div className="flex items-center gap-3 p-4 border-b">
        <h2 className="font-bold flex-1">لاگ ارسال ({items.length})</h2>
        <button onClick={load} className="border rounded-lg px-3 py-1.5 text-sm">رفرش</button>
      </div>
      {loading ? (
        <div className="p-6 text-center text-gray-400 text-sm">در حال بارگذاری...</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs text-gray-500">
              <tr>
                {['#','lead_id','تلفن','وضعیت','خطا','پیام','تاریخ'].map((h) => (
                  <th key={h} className="text-right px-3 py-2">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-8 text-gray-400">لاگی یافت نشد</td>
                </tr>
              ) : items.map((item) => (
                <tr key={item.id} className="border-t hover:bg-gray-50">
                  <td className="px-3 py-2 text-gray-400">{item.id}</td>
                  <td className="px-3 py-2">{item.lead_id}</td>
                  <td className="px-3 py-2 font-mono">{item.phone}</td>
                  <td className="px-3 py-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_COLORS[item.status.toLowerCase()] ?? "bg-gray-100 text-gray-700"}`}>
                      {item.status}
                    </span>
                  </td>
                  <td className="px-3 py-2">{item.error_msg || "—"}</td>
                  <td className="px-3 py-2 max-w-[260px] truncate">{truncateText(item.message_text)}</td>
                  <td className="px-3 py-2">{item.sent_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
