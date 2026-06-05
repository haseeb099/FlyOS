"use client";

import Link from "next/link";
import { Factory, Megaphone, Package } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { fmtGbp } from "@/lib/format";
import type { CashLeak, LeakCategory } from "@/lib/types";
import { cn } from "@/lib/utils";

const CATEGORY_META: Record<
  LeakCategory,
  { icon: LucideIcon; label: string; badgeClass: string }
> = {
  inventory: { icon: Package, label: "Inventory", badgeClass: "text-amber-400" },
  supplier_po: { icon: Factory, label: "Supplier PO", badgeClass: "text-orange-400" },
  ad_spend: { icon: Megaphone, label: "Ad spend", badgeClass: "text-blue-400" },
};

interface LeakCardProps {
  leak: CashLeak;
  onAction?: () => void;
  actionLabel?: string;
}

export function LeakCard({
  leak,
  onAction,
  actionLabel = "Generate Email",
}: LeakCardProps) {
  const meta = CATEGORY_META[leak.category];
  const Icon = meta.icon;

  return (
    <div
      className={cn(
        "group rounded-xl border border-[#222] bg-[#111] p-6 transition-colors",
        "hover:border-amber-400/40 hover:border-l-amber-400 hover:border-l-2"
      )}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex gap-3">
          <Icon className="h-6 w-6 shrink-0 text-amber-400/80" aria-hidden />
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-bold tracking-tight text-zinc-100">{leak.title}</h3>
              <Badge className={meta.badgeClass}>{meta.label}</Badge>
            </div>
            <p className="text-sm text-zinc-500 mt-0.5">{leak.subtitle}</p>
            <p className="text-sm text-zinc-400 mt-2">{leak.recommended_action}</p>
          </div>
        </div>
        <div className="text-right shrink-0">
          <p className="font-mono text-2xl font-bold text-amber-400 tabular-nums">
            {fmtGbp(leak.cash_at_risk_gbp)}
          </p>
          <p className="text-xs text-zinc-500 mt-1">{leak.units_or_days}</p>
        </div>
      </div>

      {(onAction || leak.category === "inventory") && (
        <div className="mt-4">
          {leak.category === "inventory" ? (
            <Link
              href={`/email?leak=${encodeURIComponent(leak.id)}`}
              className={cn(
                buttonVariants({ variant: "outline", size: "default" }),
                "w-full group-hover:border-amber-400/60"
              )}
            >
              {actionLabel}
            </Link>
          ) : (
            <button
              type="button"
              className={cn(
                buttonVariants({ variant: "outline", size: "default" }),
                "w-full group-hover:border-amber-400/60"
              )}
              onClick={onAction}
            >
              {leak.category === "supplier_po" ? "Chase Supplier" : "Pause Campaign"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
