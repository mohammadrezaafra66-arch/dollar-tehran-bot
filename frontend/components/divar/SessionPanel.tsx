"use client";
import { useEffect, useState, useCallback } from "react";
import { api, type DivarAccount } from "@/lib/api";

interface LoginStatus {
  likely_logged_in: boolean;
  phone: string;
  cookies_size: number;
}

export default function SessionPanel() {
  const [accounts, setAccounts] = useState<DivarAccount[]>([]);
  const [loginStatuses, setLoginStatuses] = useState<Record<string, LoginStatus>>({});
  const [loading, setLoading] = useState(false);
  const [loginModal, setLoginModal] = useState<string | null>(null);
  const [loginLoading, setLoginLoading] = useState(false);
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.divar.accounts();
      setAccounts(res.items);
      const statuses: Record<string, LoginStatus> = {};
      await Promise.all(res.items.map(async (acc) => {
        try {
          const s = await api.divar.checkLogin(acc.profile_id);
          statuses[acc.profile_id] = s;
        } catch {
          statuses[acc.profile_id] = { likely_logged_in: false, phone: "", cookies_size: 0 };
        }
      }));
      setLoginStatuses(statuses);
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { void load(); }, [load]);

  async function startLogin(profileId: string) {
    try {
      await api.divar.loginStart(profileId, "");
      setLoginLoading(true);
    } catch (err) { setMessage(err instanceof Error ? err.message : "خطا"); }
  }

  async function deleteAccount(profileId: string) {
    if (!confirm("آیا مطمئنید؟ session این پروفایل پاک میشه")) return;
    try { await api.divar.deleteAccount(profileId); await load(); }
    catch (err) { setMessage(err instanceof Error ? err.message : "خطا"); }
  }

  const reputationColor = (score: number) =>
    score > 0.7 ? "bg-green-500" : score > 0.3 ? "bg-yellow-500" : "bg-red-500";

  return (
    <div dir="rtl">
      <div className="flex justify-between items-center mb-4">
        <h2 className="font-bold text-lg">مدیریت اکانت‌های دیوار</h2>
        <button onClick={load} disabled={loading} className="border rounded-lg px-3 py-1.5 text-sm">
          {loading ? "..." : "رفرش"}
        </button>
      </div>
      {message && <div className="mb-4 p-3 bg-blue-50 text-blue-700 rounded-lg text-sm">{message}</div>}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {accounts.map(acc => {
          const status = loginStatuses[acc.profile_id];
          const isLoggedIn = status?.likely_logged_in ?? false;
          const phoneNum = status?.phone ?? "";
          return (
            <div key={acc.profile_id} className="bg-white rounded-xl border p-4">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <div className="font-bold text-sm">{acc.profile_id}</div>
                  {phoneNum && (
                    <div className="text-xs text-gray-500 mt-0.5 font-mono">{phoneNum}</div>
                  )}
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  isLoggedIn ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                }`}>
                  {isLoggedIn ? "✅ لاگین" : "❌ خارج شده"}
                </span>
              </div>
              <div className="mb-3">
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>امتیاز: {acc.reputation_score.toFixed(2)}</span>
                  <span>✅{acc.success_count} ❌{acc.failure_count}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-1.5">
                  <div className={`h-1.5 rounded-full ${reputationColor(acc.reputation_score)}`}
                    style={{ width: `${acc.reputation_score * 100}%` }} />
                </div>
              </div>
              <div className="flex gap-2">
                <button onClick={() => {
                  setLoginModal(acc.profile_id);
                  setLoginLoading(false);
                  setMessage("");
                }} className="flex-1 bg-blue-600 text-white rounded-lg py-1.5 text-xs">
                  {isLoggedIn ? "تمدید session" : "ورود"}
                </button>
                <button onClick={() => void deleteAccount(acc.profile_id)}
                  className="flex-1 bg-red-100 text-red-700 rounded-lg py-1.5 text-xs">
                  حذف
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {loginModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" dir="rtl">
          <div className="bg-white rounded-xl p-6 w-full max-w-md shadow-2xl">
            <h3 className="font-bold mb-1">ورود به دیوار</h3>
            <p className="text-xs text-gray-500 mb-4">{loginModal}</p>
            <p className="mb-4 text-sm text-gray-700">مرورگر دیوار باز می‌شود. لاگین کنید و مرورگر را ببندید.</p>
            {!loginLoading ? (
              <button onClick={() => void startLogin(loginModal)}
                className="w-full bg-blue-600 text-white rounded-lg py-2 text-sm">
                شروع لاگین
              </button>
            ) : (
              <p className="mb-4 text-sm text-blue-600">در حال انتظار برای بسته شدن مرورگر...</p>
            )}
            <button onClick={() => { setLoginModal(null); setLoginLoading(false); void load(); }}
              className="mt-4 w-full border rounded-lg py-2 text-sm text-gray-600">بستن</button>
          </div>
        </div>
      )}
    </div>
  );
}
