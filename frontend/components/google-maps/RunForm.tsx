"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { TooltipHint } from "@/components/TooltipHint";

export default function GoogleMapsRunForm() {
  const [query, setQuery] = useState("تهران کافی شاپ");
  const [running, setRunning] = useState(false);
  const [output, setOutput] = useState<string[]>([]);

  async function handleRun() {
    setRunning(true);
    try {
      const res = await api.googleMaps.run({ query });
      setOutput([res.cmd || "started"]);
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="bg-white border rounded-xl p-4" dir="rtl">
      <h3 className="font-bold text-lg mb-3">اجرا</h3>
      <TooltipHint text="کوئری جستجوی گوگل مپ را برای شروع استخراج وارد کنید." position="top">
        <label className="block text-sm text-gray-600 mb-2">کوئری جستجو</label>
      </TooltipHint>
      <input value={query} onChange={(e) => setQuery(e.target.value)} className="w-full border rounded-lg px-3 py-2 mb-3" placeholder="مثال: کافی شاپ تهران" />
      <TooltipHint text="RUN را با این کوئری برای شروع کار استخراج گوگل مپ اجرا می‌کند." position="top">
        <button onClick={handleRun} className="bg-blue-600 text-white px-4 py-2 rounded-lg" disabled={running}>
          {running ? "در حال اجرا..." : "شروع اجرا"}
        </button>
      </TooltipHint>
      {output.length > 0 && <pre className="mt-3 text-xs bg-gray-50 p-3 rounded">{output.join("\n")}</pre>}
    </div>
  );
}
