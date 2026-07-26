"use client";
import { useEffect, useState } from "react";
import { api, type TorobConfig } from "@/lib/api";

export default function TorobConfigPanel() {
  const [config, setConfig] = useState<TorobConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  async function load() {
    setLoading(true);
    try { setConfig(await api.torob.config()); }
    finally { setLoading(false); }
  }

  useEffect(() => { void load(); }, []);

  async function save() {
    if (!config) return;
    setLoading(true);
    try {
      await api.torob.saveConfig(config);
      setMessage("تنظیمات ترب با موفقیت ذخیره شد.");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "خطا");
    } finally { setLoading(false); }
  }

  if (!config) return <div className="p-6 text-center text-gray-400">در حال بارگذاری...</div>;

  const fields: { key: keyof TorobConfig; label: string }[] = [
    { key: "AFRA_API_URL", label: "آدرس API افراکالا" },
    { key: "AFRA_API_KEY", label: "کلید API افراکالا" },
    { key: "TOROB_MIN_DELAY_SECONDS", label: "حداقل تأخیر (ثانیه)" },
    { key: "TOROB_MAX_DELAY_SECONDS", label: "حداکثر تأخیر (ثانیه)" },
    { key: "TOROB_MAX_SELLERS_PER_URL", label: "حداکثر فروشنده در هر URL" },
    { key: "SELLER_CRAWL_TIMEOUT_SECONDS", label: "timeout کرال (ثانیه)" },
  ];

  return (
    <div className="bg-white rounded-xl border p-5" dir="rtl">
      <h2 className="font-bold text-lg mb-4">تنظیمات ترب</h2>
      <div className="grid gap-4 md:grid-cols-2 mb-4">
        {fields.map(({ key, label }) => (
          <label key={key} className="block">
            <span className="text-sm text-gray-600 mb-1 block">{label}</span>
            <input value={config[key]} onChange={e => setConfig({ ...config, [key]: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm" />
          </label>
        ))}
        <label className="block">
          <span className="text-sm text-gray-600 mb-1 block">کرال سایت فروشندگان</span>
          <select value={config.CRAWL_SELLER_SITES} onChange={e => setConfig({ ...config, CRAWL_SELLER_SITES: e.target.value })}
            className="w-full border rounded-lg px-3 py-2 text-sm">
            <option value="true">فعال</option>
            <option value="false">غیرفعال</option>
          </select>
        </label>
      </div>
      {message && <div className="mb-3 p-3 bg-green-50 text-green-700 rounded-lg text-sm">{message}</div>}
      <button onClick={() => void save()} disabled={loading}
        className="bg-blue-600 text-white rounded-lg px-6 py-2 text-sm disabled:opacity-50">
        {loading ? "در حال ذخیره..." : "ذخیره تنظیمات"}
      </button>
    </div>
  );
}
