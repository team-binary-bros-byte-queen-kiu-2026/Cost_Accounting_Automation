import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "ConstructAI — Georgian Construction Cost Estimator",
  description: "Upload a photo of your building project and get an instant AI-powered cost estimate.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <nav className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-50">
          <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
            <a href="/" className="flex items-center gap-2 font-bold text-lg text-white">
              <span className="text-2xl">🏗️</span>
              <span>ConstructAI</span>
            </a>
            <div className="flex gap-6 text-sm text-slate-400">
              <a href="/" className="hover:text-white transition-colors">Estimate</a>
              <a href="/admin" className="hover:text-white transition-colors">Prices</a>
            </div>
          </div>
        </nav>
        <main className="min-h-screen">{children}</main>
        <footer className="border-t border-slate-800 py-6 text-center text-sm text-slate-500">
          ConstructAI — CS-AI-2025 · Kutaisi International University · Spring 2026
        </footer>
      </body>
    </html>
  );
}
