"use client";
import { useState, useEffect, useCallback } from "react";
import { api, TorobReport } from "@/lib/api";

export default function ReportsTable() {
  const [items, setItems] = useState<TorobReport[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const limit = 20;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.torob.reports({ limit, offset });
      setItems(res.items); setTotal(res.total);
    } finally { setLoading(false); }
  }, [offset]);

  useEffect(() => { void load(); }, [load]);

  return (
    <div className="bg-white rounded-xl border mb-6">
      <div className="flex items-center gap-3 p-4 border-b">
        <h2 className="font-bold flex-1">گزارش قیمت ({total})</h2>
        <button onClick={load} className="border rounded-lg px-3 py-1.5 text-sm">رفرش</button>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs text-gray-500">
            <tr>{["#","محصول","قیمت افراکالا","کمترین رقیب","میانگین","رتبه","رقبا","اختلاف%","سینک"].map(h => (
              <th key={h} className="text-right px-3 py-2">{h}</th>
            ))}</tr>
          </thead>
          <tbody>
            {loading
              ? <tr><td colSpan={9} className="text-center py-8 text-gray-400">در حال بارگذاری...</td></tr>
              : items.length === 0
                ? <tr><td colSpan={9} className="text-center py-8 text-gray-400">موردی یافت نشد</td></tr>
                : items.map(r => (
                  <tr key={r.id} className="border-t hover:bg-gray-50">
                    <td className="px-3 py-2 text-gray-400">{r.id}</td>
                    <td className="px-3 py-2 max-w-[200px] truncate">{r.product_name}</td>
                    <td className="px-3 py-2">{r.afrakala_price?.toLocaleString()}</td>
                    <td className="px-3 py-2">{r.lowest_rival?.toLocaleString()}</td>
                    <td className="px-3 py-2">{r.avg_rival?.toFixed(0)}</td>
                    <td className="px-3 py-2">{r.afrakala_rank}</td>
                    <td className="px-3 py-2">{r.rival_count}</td>
                    <td className={`px-3 py-2 font-medium ${r.diff_percent > 0 ? "text-red-600" : "text-green-600"}`}>
                      {r.diff_percent?.toFixed(1)}%
                    </td>
                    <td className="px-3 py-2 text-xs">{r.sync_status}</td>
                  </tr>
                ))}
          </tbody>
        </table>
      </div>
      <div className="flex justify-between items-center p-3 border-t text-sm">
        <button disabled={offset === 0} onClick={() => setOffset(o => Math.max(0, o - limit))} className="px-3 py-1 border rounded disabled:opacity-40">قبلی</button>
        <span className="text-gray-500">{offset + 1}–{Math.min(offset + limit, total)} از {total}</span>
        <button disabled={offset + limit >= total} onClick={() => setOffset(o => o + limit)} className="px-3 py-1 border rounded disabled:opacity-40">بعدی</button>
      </div>
    </div>
  );
}
