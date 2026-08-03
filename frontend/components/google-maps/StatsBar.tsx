import type { GoogleMapsStats } from "@/lib/api";

export default function GoogleMapsStatsBar({ stats }: { stats: GoogleMapsStats }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
      <div className="bg-white rounded-xl border p-4">
        <div className="text-xs text-gray-500">کل رکوردها</div>
        <div className="text-2xl font-bold text-gray-900">{stats.total_records}</div>
      </div>
      <div className="bg-white rounded-xl border p-4">
        <div className="text-xs text-gray-500">ثبت‌شده</div>
        <div className="text-2xl font-bold text-green-600">{stats.synced}</div>
      </div>
      <div className="bg-white rounded-xl border p-4">
        <div className="text-xs text-gray-500">در انتظار</div>
        <div className="text-2xl font-bold text-amber-600">{stats.pending}</div>
      </div>
      <div className="bg-white rounded-xl border p-4">
        <div className="text-xs text-gray-500">ناموفق</div>
        <div className="text-2xl font-bold text-red-600">{stats.failed}</div>
      </div>
    </div>
  );
}
