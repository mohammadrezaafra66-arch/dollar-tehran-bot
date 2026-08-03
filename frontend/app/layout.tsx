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
        <nav className="bg-white border-b px-6 py-3 flex gap-6 items-center sticky top-0 z-10">
          <Link href="/" className="font-bold text-gray-900">افراکالا</Link>
          <Link href="/" className="text-sm text-gray-600 hover:text-blue-600">داشبورد</Link>
          <Link href="/divar" className="text-sm text-gray-600 hover:text-blue-600">دیوار</Link>
          <Link href="/torob" className="text-sm text-gray-600 hover:text-blue-600">ترب</Link>
          <Link href="/google-maps" className="text-sm text-gray-600 hover:text-blue-600">گوگل مپ</Link>
          <Link href="/help" className="text-sm text-gray-600 hover:text-blue-600">راهنما</Link>
        </nav>
        {children}
      </body>
    </html>
  );
}
