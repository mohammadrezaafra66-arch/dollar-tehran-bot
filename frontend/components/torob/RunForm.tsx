"use client";
import { useState } from "react";
import { api, RunResponse } from "@/lib/api";

export default function TorobRunForm() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<RunResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleRun() {
    if (!query.trim()) return;
    setLoading(true); setError(null); setResult(null);
    try {
      const res = await api.torob.run({ query });
      setResult(res);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "خطا");
    } finally { setLoading(false); }
  }

  return (
    <div className="bg-white rounded-xl border p-5 mb-6">
      <h2 className="font-bold text-lg mb-4">جستجو در ترب</h2>
      <div className="space-y-3">
        <div>
          <label className="text-sm text-gray-600 block mb-1">کلمه جستجو</label>
          <input value={query} onChange={e => setQuery(e.target.value)}
            className="w-full border rounded-lg px-3 py-2 text-sm"
            placeholder="مثال: اسپیکر بلوتوث" />
        </div>
        <button onClick={handleRun} disabled={loading}
          className="bg-blue-600 text-white rounded-lg px-5 py-2 text-sm disabled:opacity-50">
          {loading ? "در حال جستجو..." : "شروع جستجو"}
        </button>
      </div>
      {result && (
        <div className="mt-3 p-3 bg-green-50 rounded-lg text-sm text-green-800">
          ✅ اجرا شروع شد — PID: {result.pid}
          <div className="font-mono text-xs mt-1 opacity-75">{result.cmd}</div>
        </div>
      )}
      {error && <div className="mt-3 p-3 bg-red-50 rounded-lg text-sm text-red-700">{error}</div>}
    </div>
  );
}
