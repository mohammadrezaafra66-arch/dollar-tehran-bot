"use client";
import { useState, useEffect, useCallback } from "react";
import { api, DivarLead } from "@/lib/api";

const STATUS_COLORS: Record<string, string> = {
  ok: "bg-green-100 text-green-700",
  pending: "bg-yellow-100 text-yellow-700",
  failed: "bg-red-100 text-red-700",
};

export default function LeadsTable() {
  const [items, setItems] = useState<DivarLead[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const limit = 20;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.divar.leads({ limit, offset, status: status || undefined });
      setItems(res.items); setTotal(res.total);
    } finally { setLoading(false); }
  }, [offset, status]);

  useEffect(() => { void load(); }, [load]);

  return (
    <div className="bg-white rounded-xl border mb-6" dir="rtl">
      <div className="flex items-center gap-3 p-4 border-b flex-wrap">
        <h2 className="font-bold flex-1">لیدهای دیوار ({total})</h2>
        <select value={status} onChange={e => { setOffset(0); setStatus(e.target.value); }}
          className="border rounded-lg px-3 py-1.5 text-sm">
          <option value="">همه وضعیت‌ها</option>
          <option value="ok">موفق</option>
          <option value="pending">در انتظار</option>
          <option value="failed">ناموفق</option>
        </select>
        <button onClick={load} className="border rounded-lg px-3 py-1.5 text-sm">رفرش</button>
      </div>
      {loading ? <div className="p-6 text-center text-gray-400 text-sm">در حال بارگذاری...</div> : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs text-gray-500">
              <tr>
                {["#","عنوان","فروشنده","تلفن","شهر","قیمت","وضعیت","پیام","پروفایل","منبع"].map(h => (
                  <th key={h} className="text-right px-3 py-2">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr><td colSpan={10} className="text-center py-8 text-gray-400">موردی یافت نشد</td></tr>
              ) : items.map(lead => (
                <tr key={lead.id} className="border-t hover:bg-gray-50">
                  <td className="px-3 py-2 text-gray-400">{lead.id}</td>
                  <td className="px-3 py-2 max-w-[180px] truncate" title={lead.title}>{lead.title}</td>
                  <td className="px-3 py-2 max-w-[100px] truncate">{lead.seller_name}</td>
                  <td className="px-3 py-2 font-mono text-xs">{lead.phone || "—"}</td>
                  <td className="px-3 py-2">{lead.city || "—"}</td>
                  <td className="px-3 py-2 text-xs">{lead.price_text || "—"}</td>
                  <td className="px-3 py-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_COLORS[lead.extraction_status] ?? "bg-gray-100 text-gray-600"}`}>
                      {lead.extraction_status}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-center">{lead.message_sent ? "✅" : "—"}</td>
                  <td className="px-3 py-2">
                    <span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full">
                      {lead.profile_id || "—"}
                    </span>
                  </td>
                  <td className="px-3 py-2">
                    <a href={lead.source_url} target="_blank" className="text-blue-600 text-xs underline">لینک</a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="flex justify-between items-center p-3 border-t text-sm">
        <button disabled={offset === 0} onClick={() => setOffset(o => Math.max(0, o - limit))}
          className="px-3 py-1 border rounded disabled:opacity-40">قبلی</button>
        <span className="text-gray-500">{offset + 1}–{Math.min(offset + limit, total)} از {total}</span>
        <button disabled={offset + limit >= total} onClick={() => setOffset(o => o + limit)}
          className="px-3 py-1 border rounded disabled:opacity-40">بعدی</button>
      </div>
    </div>
  );
}
