"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface SessionStatus {
  logged_in: boolean;
  profile_path: string;
  session_files_found: number;
  numbered_profiles: {
    profile_id: string;
    reputation_score: number;
    success_count: number;
    failure_count: number;
    available: boolean;
  }[];
  login_instructions: string[];
}

export default function SessionPanel() {
  const [status, setStatus] = useState<SessionStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [phone, setPhone] = useState("09XXXXXXXXX");
  const [message, setMessage] = useState("");

  async function refreshStatus() {
    setLoading(true);
    try {
      const res = await api.divar.sessionStatus();
      setStatus(res);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refreshStatus();
  }, []);

  async function handleLogin() {
    if (!phone.trim()) return;
    setLoading(true);
    try {
      const res = await api.divar.login(phone.trim());
      setMessage(res.message);
    } finally {
      setLoading(false);
    }
  }

  const loggedIn = Boolean(status?.logged_in && status.session_files_found > 0);

  return (
    <div className="bg-white rounded-xl border p-5 mb-6" dir="rtl">
      <div className={`rounded-lg border px-4 py-3 mb-4 ${loggedIn ? "bg-green-50 border-green-200 text-green-800" : "bg-orange-50 border-orange-200 text-orange-800"}`}>
        {loggedIn ? "✅ احتمالاً به دیوار وارد شده‌اید — session فعال است" : "⚠️ session دیوار یافت نشد — شماره تلفن‌ها استخراج نخواهند شد"}
      </div>

      <div className="flex flex-wrap items-center gap-3 mb-4">
        <button onClick={() => void refreshStatus()} className="border rounded-lg px-3 py-2 text-sm" disabled={loading}>
          {loading ? "در حال بررسی..." : "🔄 بررسی مجدد وضعیت"}
        </button>
        <div className="text-xs text-gray-500">مسیر پروفایل: {status?.profile_path || "—"}</div>
      </div>

      {!loggedIn && (
        <div className="space-y-3 text-sm text-gray-700">
          <div className="rounded-lg border bg-gray-900 text-gray-100 p-3">
            <div className="font-semibold mb-2">برای ورود به دیوار مراحل زیر را دنبال کنید:</div>
            <ol className="list-decimal list-inside space-y-1 text-xs font-mono">
              {status?.login_instructions?.map((step, index) => (
                <li key={step}>{index + 1}. {step}</li>
              ))}
            </ol>
          </div>

          <div className="rounded-lg border border-dashed p-3 text-xs font-mono bg-gray-50 text-gray-800">
            cd /workspaces/old-dollar-tehran-bot && python3 divar-bot/run.py --login --phone 09XXXXXXXXX
          </div>

          <div className="text-xs text-gray-600">⚠️ این دستور نیاز به مرورگر گرافیکی دارد — در محیط Codespace باید از xvfb-run استفاده کنید یا session را از محیط local انتقال دهید</div>

          <div className="flex flex-col sm:flex-row gap-2">
            <input
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className="border rounded-lg px-3 py-2 text-sm w-full sm:w-64"
              placeholder="09XXXXXXXXX"
            />
            <button onClick={() => void handleLogin()} className="bg-blue-600 text-white rounded-lg px-3 py-2 text-sm" disabled={loading}>
              شروع ورود
            </button>
          </div>

          {message && <div className="rounded-lg border border-blue-200 bg-blue-50 p-3 text-xs whitespace-pre-line">{message}</div>}
        </div>
      )}

      {status?.numbered_profiles && status.numbered_profiles.length > 0 && (
        <div className="mt-4">
          <div className="text-sm font-semibold mb-2">پروفایل‌های دیوار</div>
          <div className="overflow-x-auto rounded-lg border">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50 text-gray-700">
                <tr>
                  <th className="px-3 py-2 text-right">profile_id</th>
                  <th className="px-3 py-2 text-right">reputation</th>
                  <th className="px-3 py-2 text-right">موفق</th>
                  <th className="px-3 py-2 text-right">ناموفق</th>
                  <th className="px-3 py-2 text-right">وضعیت</th>
                </tr>
              </thead>
              <tbody>
                {status.numbered_profiles.map((profile) => {
                  const reputationClass = profile.reputation_score > 0.7 ? "text-green-700" : profile.reputation_score >= 0.3 ? "text-yellow-700" : "text-red-700";
                  return (
                    <tr key={profile.profile_id} className="border-t bg-white text-gray-800">
                      <td className="px-3 py-2">{profile.profile_id}</td>
                      <td className={`px-3 py-2 font-medium ${reputationClass}`}>{profile.reputation_score.toFixed(2)}</td>
                      <td className="px-3 py-2">{profile.success_count}</td>
                      <td className="px-3 py-2">{profile.failure_count}</td>
                      <td className="px-3 py-2">{profile.available ? "در دسترس" : "استراحت"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
