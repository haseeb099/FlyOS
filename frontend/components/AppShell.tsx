"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Database,
  FileText,
  LayoutDashboard,
} from "lucide-react";

import { ReconciliationBadge } from "@/components/ReconciliationBadge";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Action Center", icon: LayoutDashboard },
  { href: "/briefing", label: "Briefing", icon: FileText },
  { href: "/backtest", label: "Backtest", icon: BarChart3 },
  { href: "/data", label: "Data", icon: Database },
];

interface AppShellProps {
  children: React.ReactNode;
  kpiStrip?: React.ReactNode;
}

export function AppShell({ children, kpiStrip }: AppShellProps) {
  const pathname = usePathname();

  return (
    <div className="flex min-h-screen">
      <aside className="hidden lg:flex w-60 shrink-0 flex-col border-r border-[#222] bg-[#0a0a0a]">
        <div className="border-b border-[#222] px-5 py-6">
          <Link href="/" className="block">
            <span className="text-xl font-bold tracking-tight text-zinc-100">
              Fly<span className="text-amber-400">OS</span>
            </span>
            <p className="text-xs text-zinc-500 mt-1">Pretty Fly · Jun 2026</p>
          </Link>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {NAV.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
                  active
                    ? "bg-amber-400/15 text-amber-400"
                    : "text-zinc-400 hover:bg-[#111] hover:text-zinc-200"
                )}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="border-t border-[#222] p-4 space-y-3">
          <ReconciliationBadge />
          <p className="text-[10px] text-zinc-600 leading-relaxed">
            Dataset as of 1 Jun 2026 · verified against bank_transactions.csv
          </p>
        </div>
      </aside>

      <div className="flex flex-1 flex-col min-w-0">
        <header className="lg:hidden border-b border-[#222] px-4 py-4 flex items-center justify-between">
          <Link href="/" className="text-lg font-bold">
            Fly<span className="text-amber-400">OS</span>
          </Link>
          <ReconciliationBadge />
        </header>

        {kpiStrip}

        <main className="flex-1 px-4 py-6 lg:px-8">{children}</main>

        <footer className="border-t border-[#222] px-6 py-4 text-center text-xs text-zinc-600">
          Powered by Wayflyer × Fin · Data verified against bank_transactions
        </footer>
      </div>
    </div>
  );
}

export function MobileNav() {
  const pathname = usePathname();
  return (
    <nav className="lg:hidden flex gap-1 mb-6 overflow-x-auto pb-1">
      {NAV.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className={cn(
            "shrink-0 rounded-lg px-3 py-1.5 text-xs",
            pathname === item.href
              ? "bg-amber-400/15 text-amber-400"
              : "text-zinc-500"
          )}
        >
          {item.label}
        </Link>
      ))}
    </nav>
  );
}
