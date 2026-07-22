import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "پنل افراکالا",
  description: "کنترل پنل ربات‌های افراکالا",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fa" dir="rtl">
      <body className="bg-gray-50">
        <nav className="bg-white border-b px-6 py-3 flex gap-4 text-sm font-medium sticky top-0 z-10">
          <span className="text-gray-400 font-bold ml-4">پنل افراکالا</span>
          <Link href="/divar" className="text-gray-700 hover:text-blue-600">دیوار</Link>
          <Link href="/torob" className="text-gray-700 hover:text-blue-600">ترب</Link>
        </nav>
        {children}
      </body>
    </html>
  );
}
