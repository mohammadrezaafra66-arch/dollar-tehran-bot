"use client";
import { useEffect, useState } from "react";
import { api, type DivarConfig } from "@/lib/api";

export default function ConfigPanel() {
  const [config, setConfig] = useState<DivarConfig | null>(null);
  const [template, setTemplate] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  async function load() {
    setLoading(true);
    try {
      const [cfg, tmpl] = await Promise.all([api.divar.config(), api.divar.template()]);
      setConfig(cfg);
      setTemplate(tmpl.template);
    } finally { setLoading(false); }
  }

  useEffect(() => { void load(); }, []);

  async function save() {
    if (!config) return;
    setLoading(true);
    try {
      await Promise.all([api.divar.saveConfig(config), api.divar.saveTemplate(template)]);
      setMessage("تنظیمات با موفقیت ذخیره شد.");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "خطا");
    } finally { setLoading(false); }
  }

  if (!config) return <div className="p-6 text-center text-gray-400">در حال بارگذاری...</div>;

  const fields: { key: keyof DivarConfig; label: string; type?: string }[] = [
    { key: "DIVAR_MAX_ADS_PER_RUN", label: "حداکثر آگهی در هر اجرا" },
    { key: "DIVAR_DAILY_MESSAGE_LIMIT", label: "محدودیت پیام روزانه" },
    { key: "DIVAR_MIN_DELAY_SECONDS", label: "حداقل تأخیر (ثانیه)" },
    { key: "DIVAR_MAX_DELAY_SECONDS", label: "حداکثر تأخیر (ثانیه)" },
    { key: "HTTP_PROXY", label: "پروکسی HTTP" },
    { key: "DEEPSEEK_API_KEY", label: "کلید API دیپ‌سیک", type: "password" },
    { key: "AFRA_API_URL", label: "آدرس API افراکالا" },
  ];

  return (
    <div className="space-y-6" dir="rtl">
      <div className="bg-white rounded-xl border p-5">
        <h2 className="font-bold text-lg mb-4">تنظیمات دیوار</h2>
        <div className="grid gap-4 md:grid-cols-2">
          {fields.map(({ key, label, type }) => (
            <label key={key} className="block">
              <span className="text-sm text-gray-600 mb-1 block">{label}</span>
              <input type={type ?? "text"} value={config[key]}
                onChange={e => setConfig({ ...config, [key]: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
            </label>
          ))}
        </div>
      </div>
      <div className="bg-white rounded-xl border p-5">
        <h2 className="font-bold text-lg mb-2">قالب پیام</h2>
        <p className="text-xs text-gray-500 mb-3">متغیرها: {"{name}"}, {"{category}"}, {"{city}"}, {"{title}"}</p>
        <textarea value={template} onChange={e => setTemplate(e.target.value)} rows={6}
          className="w-full border rounded-lg px-3 py-2 text-sm font-mono" />
      </div>
      {message && <div className="p-3 bg-green-50 text-green-700 rounded-lg text-sm">{message}</div>}
      <button onClick={() => void save()} disabled={loading}
        className="bg-blue-600 text-white rounded-lg px-6 py-2 text-sm disabled:opacity-50">
        {loading ? "در حال ذخیره..." : "ذخیره تنظیمات"}
      </button>
    </div>
  );
}
