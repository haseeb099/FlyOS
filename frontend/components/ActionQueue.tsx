"use client";

import { Factory, Megaphone, Package } from "lucide-react";

import { ConfidenceBadge } from "@/components/ConfidenceBadge";
import { Badge } from "@/components/ui/badge";
import { fmtGbp } from "@/lib/format";
import type { ActionItem, LeakCategory } from "@/lib/types";
import { cn } from "@/lib/utils";

const CATEGORY_META: Record<
  LeakCategory,
  { Icon: typeof Package; label: string; badgeClass: string }
> = {
  inventory: { Icon: Package, label: "Inventory", badgeClass: "text-amber-400" },
  supplier_po: { Icon: Factory, label: "Supplier PO", badgeClass: "text-orange-400" },
  ad_spend: { Icon: Megaphone, label: "Ad spend", badgeClass: "text-blue-400" },
};

interface ActionQueueProps {
  actions: ActionItem[];
  selectedId: string | null;
  actionedIds: string[];
  filter: LeakCategory | "all";
  onSelect: (id: string) => void;
  onFilterChange: (filter: LeakCategory | "all") => void;
}

export function ActionQueue({
  actions,
  selectedId,
  actionedIds,
  filter,
  onSelect,
  onFilterChange,
}: ActionQueueProps) {
  const filtered =
    filter === "all" ? actions : actions.filter((a) => a.leak.category === filter);

  const tabs: Array<{ key: LeakCategory | "all"; label: string }> = [
    { key: "all", label: "All" },
    { key: "inventory", label: "Inventory" },
    { key: "supplier_po", label: "POs" },
    { key: "ad_spend", label: "Ads" },
  ];

  return (
    <div className="flex flex-col h-full">
      <div className="flex gap-1 mb-4 flex-wrap">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => onFilterChange(tab.key)}
            className={cn(
              "rounded-lg px-3 py-1 text-xs transition-colors",
              filter === tab.key
                ? "bg-amber-400/15 text-amber-400"
                : "text-zinc-500 hover:text-zinc-300"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="space-y-2 flex-1 overflow-y-auto max-h-[600px] pr-1">
        {filtered.length === 0 ? (
          <p className="text-sm text-zinc-500 py-8 text-center">No actions in this category.</p>
        ) : (
          filtered.map((action, idx) => {
            const { leak } = action;
            const meta = CATEGORY_META[leak.category];
            const Icon = meta.Icon;
            const isActioned = actionedIds.includes(leak.id);
            const isSelected = selectedId === leak.id;

            return (
              <button
                key={leak.id}
                type="button"
                onClick={() => onSelect(leak.id)}
                style={{ animationDelay: `${idx * 50}ms` }}
                className={cn(
                  "action-queue-item w-full text-left rounded-xl border p-4 transition-all",
                  isSelected
                    ? "border-amber-400/50 bg-amber-400/5"
                    : "border-[#222] bg-[#111] hover:border-[#333]",
                  isActioned && "opacity-50"
                )}
              >
                <div className="flex items-start gap-3">
                  <span className="font-mono text-xs text-zinc-600 mt-1">#{action.rank}</span>
                  <Icon className={cn("h-5 w-5 mt-0.5", meta.badgeClass)} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span
                        className={cn(
                          "font-medium text-zinc-100 truncate",
                          isActioned && "line-through"
                        )}
                      >
                        {leak.title}
                      </span>
                      <Badge className={meta.badgeClass}>{meta.label}</Badge>
                      <ConfidenceBadge confidence={leak.confidence} />
                    </div>
                    <p className="text-xs text-zinc-500 mt-0.5 truncate">{leak.subtitle}</p>
                    <p className="font-mono text-sm text-amber-400 mt-1 tabular-nums">
                      {fmtGbp(leak.recoverable_gbp)} recoverable
                    </p>
                  </div>
                </div>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}
