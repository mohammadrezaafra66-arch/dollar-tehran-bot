"use client";
import { DivarStats } from "@/lib/api";

interface Props { stats: DivarStats }

const cards = [
  { key: "total_leads", label: "کل لیدها", color: "bg-blue-50 text-blue-700" },
  { key: "synced", label: "سینک‌شده", color: "bg-green-50 text-green-700" },
  { key: "messages_sent", label: "پیام ارسال‌شده", color: "bg-purple-50 text-purple-700" },
  { key: "pending", label: "در انتظار", color: "bg-yellow-50 text-yellow-700" },
  { key: "failed", label: "ناموفق", color: "bg-red-50 text-red-700" },
] as const;

export default function StatsBar({ stats }: Props) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-6">
      {cards.map(({ key, label, color }) => (
        <div key={key} className={`rounded-xl p-4 ${color}`}>
          <div className="text-2xl font-bold">{stats[key]}</div>
          <div className="text-xs mt-1 opacity-75">{label}</div>
        </div>
      ))}
    </div>
  );
}
