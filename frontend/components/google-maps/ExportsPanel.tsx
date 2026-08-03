"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function GoogleMapsExportsPanel() {
  const [items, setItems] = useState<string[]>([]);

  useEffect(() => {
    api.googleMaps.exports().then((res) => setItems(res.files)).catch(() => setItems([]));
  }, []);

  return (
    <div className="bg-white border rounded-xl p-4" dir="rtl">
      <h3 className="font-bold text-lg mb-3">خروجی‌ها</h3>
      <ul className="space-y-2 text-sm">
        {items.length === 0 && <li className="text-gray-400">هیچ خروجی‌ای وجود ندارد</li>}
        {items.map((item) => (
          <li key={item} className="bg-gray-50 rounded p-2">{item}</li>
        ))}
      </ul>
    </div>
  );
}
