"use client";
import { useEffect, useState, useCallback } from "react";
import { api, type DivarAccount } from "@/lib/api";

export default function SessionPanel() {
  const [accounts, setAccounts] = useState<DivarAccount[]>([]);
  const [loading, setLoading] = useState(false);
  const [loginModal, setLoginModal] = useState<string | null>(null);
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");
  const [loginStep, setLoginStep] = useState<"phone"|"otp"|"done">("phone");
  const [loginOutput, setLoginOutput] = useState<string[]>([]);
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try { const res = await api.divar.accounts(); setAccounts(res.items); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { void load(); }, [load]);

  async function startLogin(profileId: string) {
    if (!phone.trim()) return;
    try {
      await api.divar.loginStart(profileId, phone);
      setLoginStep("otp");
      pollStatus(profileId);
    } catch (err) { setMessage(err instanceof Error ? err.message : "خطا"); }
  }

  function pollStatus(profileId: string) {
    const interval = setInterval(async () => {
      const res = await api.divar.loginStatus(profileId);
      setLoginOutput(res.output);
      if (!res.running) {
        clearInterval(interval);
        if (res.success) { setLoginStep("done"); setTimeout(() => { setLoginModal(null); void load(); }, 2000); }
      }
    }, 2000);
  }

  async function sendOtp(profileId: string) {
    try { await api.divar.loginOtp(profileId, otp); setMessage("OTP ارسال شد"); }
    catch (err) { setMessage(err instanceof Error ? err.message : "خطا"); }
  }

  async function deleteAccount(profileId: string) {
    if (!confirm("آیا مطمئنید؟")) return;
    try { await api.divar.deleteAccount(profileId); await load(); }
    catch (err) { setMessage(err instanceof Error ? err.message : "خطا"); }
  }

  const reputationColor = (score: number) =>
    score > 0.7 ? "bg-green-500" : score > 0.3 ? "bg-yellow-500" : "bg-red-500";

  return (
    <div dir="rtl">
      {message && <div className="mb-4 p-3 bg-blue-50 text-blue-700 rounded-lg text-sm">{message}</div>}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {accounts.map(acc => (
          <div key={acc.profile_id} className="bg-white rounded-xl border p-4">
            <div className="flex justify-between items-start mb-3">
              <div>
                <div className="font-bold text-sm">{acc.profile_id}</div>
                <span className={`text-xs px-2 py-0.5 rounded-full ${acc.available ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
                  {acc.available ? "فعال" : "در cooldown"}
                </span>
              </div>
              <span className={`text-xs px-2 py-0.5 rounded-full ${acc.has_session_files ? "bg-blue-100 text-blue-700" : "bg-gray-100 text-gray-500"}`}>
                {acc.has_session_files ? "session دارد" : "بدون session"}
              </span>
            </div>
            <div className="mb-3">
              <div className="flex justify-between text-xs text-gray-500 mb-1">
                <span>امتیاز: {acc.reputation_score.toFixed(2)}</span>
                <span>✅{acc.success_count} ❌{acc.failure_count}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className={`h-2 rounded-full ${reputationColor(acc.reputation_score)}`}
                  style={{ width: `${acc.reputation_score * 100}%` }} />
              </div>
            </div>
            <div className="flex gap-2">
              <button onClick={() => { setLoginModal(acc.profile_id); setLoginStep("phone"); setLoginOutput([]); setOtp(""); setPhone(""); }}
                className="flex-1 bg-blue-600 text-white rounded-lg py-1.5 text-xs">ورود</button>
              <button onClick={() => void deleteAccount(acc.profile_id)}
                className="flex-1 bg-red-100 text-red-700 rounded-lg py-1.5 text-xs">حذف</button>
            </div>
          </div>
        ))}
      </div>

      {loginModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" dir="rtl">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <h3 className="font-bold mb-4">ورود به دیوار — {loginModal}</h3>
            {loginStep === "phone" && (
              <div className="space-y-3">
                <input value={phone} onChange={e => setPhone(e.target.value)} placeholder="09XXXXXXXXX"
                  className="w-full border rounded-lg px-3 py-2 text-sm" />
                <button onClick={() => void startLogin(loginModal)}
                  className="w-full bg-blue-600 text-white rounded-lg py-2 text-sm">شروع لاگین</button>
              </div>
            )}
            {loginStep === "otp" && (
              <div className="space-y-3">
                <pre className="bg-gray-950 text-green-400 text-xs p-3 rounded-lg max-h-40 overflow-auto">{loginOutput.join("\n")}</pre>
                <input value={otp} onChange={e => setOtp(e.target.value)} placeholder="کد OTP"
                  className="w-full border rounded-lg px-3 py-2 text-sm" />
                <button onClick={() => void sendOtp(loginModal)}
                  className="w-full bg-green-600 text-white rounded-lg py-2 text-sm">تأیید کد</button>
              </div>
            )}
            {loginStep === "done" && <div className="text-center text-green-600 font-bold">✅ لاگین موفق!</div>}
            <button onClick={() => setLoginModal(null)} className="mt-3 w-full border rounded-lg py-2 text-sm text-gray-600">بستن</button>
          </div>
        </div>
      )}
    </div>
  );
}
