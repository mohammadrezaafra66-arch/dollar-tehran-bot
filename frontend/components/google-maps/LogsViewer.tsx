"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function GoogleMapsLogsViewer() {
  const [lines, setLines] = useState<string[]>([]);

  useEffect(() => {
    api.googleMaps.logs(100).then((res) => setLines(res.logs)).catch(() => setLines([]));
  }, []);

  return (
    <div className="bg-white border rounded-xl p-4" dir="rtl">
      <h3 className="font-bold text-lg mb-3">لاگ‌ها</h3>
      <pre className="text-xs bg-gray-50 rounded p-3 max-h-96 overflow-auto">{lines.join("\n") || "لاگی موجود نیست"}</pre>
    </div>
  );
}
