"use client";
import { useState } from "react";
import { TooltipHint } from "@/components/TooltipHint";

export default function GoogleMapsConfigPanel() {
  const [enabled, setEnabled] = useState(true);

  return (
    <div className="bg-white border rounded-xl p-4" dir="rtl">
      <h3 className="font-bold text-lg mb-3">پیکربندی</h3>
      <TooltipHint text="اگر فعال باشد، موتور گوگل مپ برای اجرای جستجو و استخراج آماده است." position="top">
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} />
          فعال بودن موتور گوگل مپ
        </label>
      </TooltipHint>
    </div>
  );
}
