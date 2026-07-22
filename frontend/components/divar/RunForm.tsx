"use client";
import { useState } from "react";
import { api, type RunResponse } from "@/lib/api";

export default function RunForm() {
  const [url, setUrl] = useState("https://divar.ir/s/tehran");
  const [sendMessages, setSendMessages] = useState(false);
  const [noAi, setNoAi] = useState(false);
  const [result, setResult] = useState<RunResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleRun() {
    if (!url.trim()) return;
    setLoading(true); setError(null); setResult(null);
    try {
      const res = await api.divar.run({ url, send_messages: sendMessages, no_ai: noAi });
      setResult(res);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "خطا");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-white rounded-xl border p-5 mb-6">
      <h2 className="font-bold text-lg mb-4">اجرای ربات دیوار</h2>
      <div className="space-y-3">
        <div>
          <label className="text-sm text-gray-600 block mb-1">URL دیوار</label>
          <input
            value={url} onChange={e => setUrl(e.target.value)}
            className="w-full border rounded-lg px-3 py-2 text-sm font-mono"
            placeholder="https://divar.ir/s/tehran/mobile-phones"
          />
        </div>
        <div className="flex gap-4 text-sm">
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={sendMessages} onChange={e => setSendMessages(e.target.checked)} />
            ارسال پیام
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={noAi} onChange={e => setNoAi(e.target.checked)} />
            بدون AI
          </label>
        </div>
        <button
          onClick={handleRun} disabled={loading}
          className="bg-green-600 text-white rounded-lg px-5 py-2 text-sm disabled:opacity-50"
        >
          {loading ? "در حال اجرا..." : "شروع اجرا"}
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
