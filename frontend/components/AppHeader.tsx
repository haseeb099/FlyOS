"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { ReconciliationBadge } from "@/components/ReconciliationBadge";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Dashboard" },
  { href: "/leaks", label: "Leaks" },
  { href: "/backtest", label: "Backtest" },
  { href: "/email", label: "Email" },
];

export function AppHeader() {
  const pathname = usePathname();

  return (
    <header className="border-b border-[#222] bg-[#0a0a0a]">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <Link href="/" className="text-xl font-bold tracking-tight text-zinc-100">
            CashFly
          </Link>
          <p className="text-xs text-zinc-500 mt-0.5">Pretty Fly · Jun 2026</p>
        </div>
        <div className="flex flex-wrap items-center gap-4">
          <ReconciliationBadge />
          <nav className="flex gap-1">
            {NAV.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "rounded-lg px-3 py-1.5 text-sm transition-colors",
                  pathname === item.href
                    ? "bg-amber-400/15 text-amber-400"
                    : "text-zinc-400 hover:text-zinc-200"
                )}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </div>
    </header>
  );
}
