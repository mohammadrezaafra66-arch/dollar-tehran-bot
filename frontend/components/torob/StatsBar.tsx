"use client";
import { TorobStats } from "@/lib/api";

const cards = [
  { key: "total_sellers", label: "کل فروشندگان", color: "bg-blue-50 text-blue-700" },
  { key: "synced", label: "سینک‌شده", color: "bg-green-50 text-green-700" },
  { key: "total_reports", label: "گزارش قیمت", color: "bg-purple-50 text-purple-700" },
  { key: "total_history", label: "تاریخچه قیمت", color: "bg-orange-50 text-orange-700" },
] as const;

export default function TorobStatsBar({ stats }: { stats: TorobStats }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
      {cards.map(({ key, label, color }) => (
        <div key={key} className={`rounded-xl p-4 ${color}`}>
          <div className="text-2xl font-bold">{stats[key]}</div>
          <div className="text-xs mt-1 opacity-75">{label}</div>
        </div>
      ))}
    </div>
  );
}
