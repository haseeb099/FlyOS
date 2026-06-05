"use client";

import { fmtGbp } from "@/lib/format";
import type { Breakdown, CashPosition } from "@/lib/types";

interface KpiStripProps {
  totalRecoverable: number;
  cashPosition: CashPosition | null;
  actionCount: number;
  breakdown: Breakdown | null;
}

export function KpiStrip({
  totalRecoverable,
  cashPosition,
  actionCount,
  breakdown,
}: KpiStripProps) {
  const items = [
    {
      label: "Recoverable",
      value: fmtGbp(totalRecoverable),
      accent: true,
    },
    {
      label: "Net cash",
      value: cashPosition ? fmtGbp(cashPosition.net_cash_gbp) : "—",
    },
    {
      label: "Actions",
      value: String(actionCount),
    },
    {
      label: "Inventory · PO · Ads",
      value: breakdown
        ? `${fmtGbp(breakdown.inventory_gbp)} · ${fmtGbp(breakdown.supplier_gbp)} · ${fmtGbp(breakdown.ads_gbp)}`
        : "—",
      small: true,
    },
  ];

  return (
    <div className="border-b border-[#222] bg-[#0a0a0a]/80 backdrop-blur">
      <div className="mx-auto flex max-w-[1400px] flex-wrap gap-4 px-4 py-4 lg:px-8">
        {items.map((item) => (
          <div key={item.label} className="min-w-[120px] flex-1">
            <p className="text-[10px] uppercase tracking-widest text-zinc-500">
              {item.label}
            </p>
            <p
              className={
                item.accent
                  ? "font-mono text-2xl font-bold text-amber-400 tabular-nums"
                  : item.small
                    ? "font-mono text-sm text-zinc-400 tabular-nums"
                    : "font-mono text-xl font-semibold text-zinc-200 tabular-nums"
              }
            >
              {item.value}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
