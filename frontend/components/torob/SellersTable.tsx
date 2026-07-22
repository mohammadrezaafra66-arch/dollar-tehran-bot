"use client";
import { useState, useEffect, useCallback } from "react";
import { api, TorobSeller } from "@/lib/api";

export default function SellersTable() {
  const [items, setItems] = useState<TorobSeller[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const limit = 20;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.torob.sellers({ limit, offset });
      setItems(res.items); setTotal(res.total);
    } finally { setLoading(false); }
  }, [offset]);

  useEffect(() => { void load(); }, [load]);

  return (
    <div className="bg-white rounded-xl border mb-6">
      <div className="flex items-center gap-3 p-4 border-b">
        <h2 className="font-bold flex-1">فروشندگان ترب ({total})</h2>
        <button onClick={load} className="border rounded-lg px-3 py-1.5 text-sm">رفرش</button>
      </div>
      {loading ? <div className="p-6 text-center text-gray-400 text-sm">در حال بارگذاری...</div> : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs text-gray-500">
              <tr>{["#","فروشگاه","تلفن","ایمیل","قیمت","اینستاگرام","تلگرام","وضعیت","سینک"].map(h => (
                <th key={h} className="text-right px-3 py-2">{h}</th>
              ))}</tr>
            </thead>
            <tbody>
              {items.length === 0
                ? <tr><td colSpan={9} className="text-center py-8 text-gray-400">موردی یافت نشد</td></tr>
                : items.map(s => (
                  <tr key={s.id} className="border-t hover:bg-gray-50">
                    <td className="px-3 py-2 text-gray-400">{s.id}</td>
                    <td className="px-3 py-2 max-w-[160px] truncate">
                      {s.store_url ? <a href={s.store_url} target="_blank" className="text-blue-600 underline">{s.store_name}</a> : s.store_name}
                    </td>
                    <td className="px-3 py-2 font-mono text-xs">{s.phone || "—"}</td>
                    <td className="px-3 py-2 text-xs">{s.email || "—"}</td>
                    <td className="px-3 py-2">{s.price_on_torob?.toLocaleString() || "—"}</td>
                    <td className="px-3 py-2 text-xs">{s.instagram || "—"}</td>
                    <td className="px-3 py-2 text-xs">{s.telegram || "—"}</td>
                    <td className="px-3 py-2 text-xs">{s.crawl_status}</td>
                    <td className="px-3 py-2 text-xs">{s.sync_status}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="flex justify-between items-center p-3 border-t text-sm">
        <button disabled={offset === 0} onClick={() => setOffset(o => Math.max(0, o - limit))} className="px-3 py-1 border rounded disabled:opacity-40">قبلی</button>
        <span className="text-gray-500">{offset + 1}–{Math.min(offset + limit, total)} از {total}</span>
        <button disabled={offset + limit >= total} onClick={() => setOffset(o => o + limit)} className="px-3 py-1 border rounded disabled:opacity-40">بعدی</button>
      </div>
    </div>
  );
}
