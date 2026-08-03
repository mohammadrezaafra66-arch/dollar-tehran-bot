"use client";
import { useState, useEffect, useRef } from "react";
import { api, type RunResponse, type DivarAccount } from "@/lib/api";
import { TooltipHint } from "@/components/TooltipHint";

export default function RunForm() {
  const [url, setUrl] = useState("https://divar.ir/s/tehran");
  const [sendMessages, setSendMessages] = useState(false);
  const [noAi, setNoAi] = useState(false);
  const [profileId, setProfileId] = useState("divar-profile-1");
  const [accounts, setAccounts] = useState<DivarAccount[]>([]);
  const [result, setResult] = useState<RunResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const logsRef = useRef<HTMLPreElement>(null);
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    api.divar.accounts().then(r => setAccounts(r.items)).catch(() => null);
    checkStatus();
  }, []);

  useEffect(() => {
    if (logsRef.current) {
      logsRef.current.scrollTop = logsRef.current.scrollHeight;
    }
  }, [logs]);

  async function checkStatus() {
    try {
      const s = await api.divar.runStatus();
      setIsRunning(s.running);
      if (s.running) startPolling();
    } catch { null; }
  }

  function startPolling() {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const s = await api.divar.runStatus();
        if (s.output) setLogs(s.output);
        if (!s.running) {
          setIsRunning(false);
          setLoading(false);
          clearInterval(pollRef.current!);
        }
      } catch { null; }
    }, 3000);
  }

  async function handleRun() {
    if (!url.trim()) return;
    setLoading(true); setError(null); setResult(null); setLogs([]);
    try {
      const res = await api.divar.run({ url, send_messages: sendMessages, no_ai: noAi, profile_id: profileId });
      setResult(res);
      setIsRunning(true);
      startPolling();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "خطا");
      setLoading(false);
    }
  }

  async function handleStop() {
    try {
      await api.divar.runStop();
      setIsRunning(false);
      setLoading(false);
      if (pollRef.current) clearInterval(pollRef.current);
    } catch { null; }
  }

  return (
    <div className="space-y-4" dir="rtl">
      <div className="bg-white rounded-xl border p-5">
        <h2 className="font-bold text-lg mb-4">اجرای ربات دیوار</h2>
        <div className="space-y-4">
          <div>
            <TooltipHint text="آدرس صفحهٔ دیوار را وارد کنید تا ربات از آن شروع به استخراج لید کند." position="top">
              <label className="text-sm text-gray-600 block mb-1">URL دیوار</label>
            </TooltipHint>
            <input value={url} onChange={e => setUrl(e.target.value)}
              disabled={isRunning}
              className="w-full border rounded-lg px-3 py-2 text-sm font-mono disabled:bg-gray-50"
              placeholder="https://divar.ir/s/tehran/mobile-phones" />
          </div>
          <div>
            <TooltipHint text="اکانت یا پروفایل موردنظر برای اجرای دیوار را انتخاب کنید." position="top">
              <label className="text-sm text-gray-600 block mb-1">پروفایل (اکانت)</label>
            </TooltipHint>
            <select value={profileId} onChange={e => setProfileId(e.target.value)}
              disabled={isRunning}
              className="w-full border rounded-lg px-3 py-2 text-sm disabled:bg-gray-50">
              {accounts.map(acc => (
                <option key={acc.profile_id} value={acc.profile_id}>
                  {acc.profile_id}
                </option>
              ))}
            </select>
          </div>
          <div className="flex gap-4 text-sm">
            <TooltipHint text="اگر فعال باشد، پیام‌های ثبت‌شده برای لیدها هم ارسال می‌شوند." position="top">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={sendMessages} disabled={isRunning}
                  onChange={e => setSendMessages(e.target.checked)} />
                ارسال پیام
              </label>
            </TooltipHint>
            <TooltipHint text="در صورت فعال بودن، پردازش AI برای تحلیل لیدها غیرفعال می‌شود." position="top">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={noAi} disabled={isRunning}
                  onChange={e => setNoAi(e.target.checked)} />
                بدون AI
              </label>
            </TooltipHint>
          </div>
          <div className="flex gap-3">
            <TooltipHint text="اجرای جدید را با تنظیمات انتخاب‌شده آغاز می‌کند." position="top">
              <button onClick={handleRun} disabled={loading || isRunning}
                className="bg-green-600 text-white rounded-lg px-5 py-2 text-sm disabled:opacity-50">
                {loading ? "در حال شروع..." : "شروع اجرا"}
              </button>
            </TooltipHint>
            {isRunning && (
              <TooltipHint text="اجرای جاری را متوقف می‌کند و لاگ‌ها را قطع می‌کند." position="top">
                <button onClick={handleStop}
                  className="bg-red-600 text-white rounded-lg px-5 py-2 text-sm">
                  توقف
                </button>
              </TooltipHint>
            )}
          </div>
        </div>

        {isRunning && (
          <div className="mt-3 flex items-center gap-2 text-sm text-blue-600">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
            ربات در حال اجراست...
          </div>
        )}

        {result && !isRunning && (
          <div className="mt-3 p-3 bg-green-50 rounded-lg text-sm text-green-800">
            ✅ اجرا تموم شد — PID: {result.pid}
          </div>
        )}
        {error && <div className="mt-3 p-3 bg-red-50 rounded-lg text-sm text-red-700">{error}</div>}
      </div>

      {(isRunning || logs.length > 0) && (
        <div className="bg-white rounded-xl border">
          <div className="flex items-center justify-between p-4 border-b">
            <h3 className="font-bold text-sm">لاگ‌های زنده</h3>
            {isRunning && <span className="text-xs text-blue-500 animate-pulse">● در حال بروزرسانی</span>}
          </div>
          <pre ref={logsRef}
            className="bg-gray-950 text-green-400 text-xs p-4 rounded-b-xl overflow-auto max-h-80 font-mono leading-5">
            {logs.length === 0 ? "منتظر لاگ..." : logs.join("\n")}
          </pre>
        </div>
      )}
    </div>
  );
}
