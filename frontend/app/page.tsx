"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

import { ActionDetail } from "@/components/ActionDetail";
import { ActionQueue } from "@/components/ActionQueue";
import { AppShell, MobileNav } from "@/components/AppShell";
import { CategoryChart } from "@/components/CategoryChart";
import { DataLoader } from "@/components/DataLoader";
import { KpiStrip } from "@/components/KpiStrip";
import { useToast } from "@/components/ui/toaster";
import { getActions, getCashPosition } from "@/lib/api";
import { fmtGbp } from "@/lib/format";
import { useAppStore } from "@/lib/store";
import type { LeakCategory } from "@/lib/types";

function ActionCenterContent() {
  const searchParams = useSearchParams();
  const { toast } = useToast();
  const actions = useAppStore((s) => s.actions);
  const totalRecoverable = useAppStore((s) => s.totalRecoverable);
  const breakdown = useAppStore((s) => s.breakdown);
  const selectedActionId = useAppStore((s) => s.selectedActionId);
  const actionedIds = useAppStore((s) => s.actionedIds);
  const setActions = useAppStore((s) => s.setActions);
  const setSelectedAction = useAppStore((s) => s.setSelectedAction);
  const setCashSummary = useAppStore((s) => s.setCashSummary);

  const [filter, setFilter] = useState<LeakCategory | "all">("all");
  const [loading, setLoading] = useState(actions.length === 0);

  useEffect(() => {
    const cat = searchParams.get("category") as LeakCategory | null;
    if (cat && ["inventory", "supplier_po", "ad_spend"].includes(cat)) {
      setFilter(cat);
    }
  }, [searchParams]);

  useEffect(() => {
    if (actions.length > 0) {
      setLoading(false);
      return;
    }
    Promise.all([getActions(10), getCashPosition()])
      .then(([res, position]) => {
        setActions(
          res.actions,
          res.total_liberation_gbp,
          res.action_count,
          {
            inventory_gbp: res.breakdown.inventory_gbp ?? 0,
            supplier_gbp: res.breakdown.supplier_gbp ?? 0,
            ads_gbp: res.breakdown.ads_gbp ?? 0,
            item_count: res.breakdown.item_count ?? res.action_count,
          }
        );
        setCashSummary(
          res.total_liberation_gbp,
          res.actions.map((a) => a.leak),
          position,
          {
            inventory_gbp: res.breakdown.inventory_gbp ?? 0,
            supplier_gbp: res.breakdown.supplier_gbp ?? 0,
            ads_gbp: res.breakdown.ads_gbp ?? 0,
            item_count: res.breakdown.item_count ?? res.action_count,
          }
        );
      })
      .catch(() => setLoading(false))
      .finally(() => setLoading(false));
  }, [actions.length, setActions, setCashSummary]);

  const selectedAction = useMemo(
    () => actions.find((a) => a.leak.id === selectedActionId) ?? actions[0] ?? null,
    [actions, selectedActionId]
  );

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-16 rounded-xl bg-[#111] animate-pulse" />
        <div className="grid lg:grid-cols-2 gap-6">
          <div className="h-96 rounded-xl bg-[#111] animate-pulse" />
          <div className="h-96 rounded-xl bg-[#111] animate-pulse" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="hero-gradient rounded-2xl border border-[#222] p-8 text-center">
        <p className="text-xs uppercase tracking-widest text-zinc-500 mb-2">
          Today&apos;s Cash Liberation Opportunities
        </p>
        <p className="font-mono text-5xl lg:text-6xl font-bold text-amber-400 tabular-nums">
          {fmtGbp(totalRecoverable)}
        </p>
        <p className="text-sm text-zinc-400 mt-2">recoverable by end of June</p>
      </div>

      <MobileNav />

      <div className="grid gap-6 lg:grid-cols-[1fr_1.2fr]">
        <div className="space-y-4">
          <h2 className="text-sm font-medium text-zinc-400">Action queue</h2>
          <ActionQueue
            actions={actions}
            selectedId={selectedAction?.leak.id ?? null}
            actionedIds={actionedIds}
            filter={filter}
            onSelect={setSelectedAction}
            onFilterChange={setFilter}
          />
          <CategoryChart breakdown={breakdown} />
        </div>
        <div>
          <h2 className="text-sm font-medium text-zinc-400 mb-4">Action detail</h2>
          <ActionDetail
            action={selectedAction}
            onSimulated={(msg) => toast(msg, "success")}
          />
        </div>
      </div>
    </div>
  );
}

export default function ActionCenterPage() {
  const isDataLoaded = useAppStore((s) => s.isDataLoaded);
  const bootstrapping = useAppStore((s) => s.bootstrapping);
  const totalRecoverable = useAppStore((s) => s.totalRecoverable);
  const cashPosition = useAppStore((s) => s.cashPosition);
  const leakCount = useAppStore((s) => s.leakCount);
  const breakdown = useAppStore((s) => s.breakdown);

  if (bootstrapping) {
    return (
      <AppShell>
        <div className="py-24 text-center text-zinc-500">Syncing with API…</div>
      </AppShell>
    );
  }

  if (!isDataLoaded) {
    return (
      <AppShell>
        <div className="max-w-xl mx-auto py-12">
          <h1 className="text-3xl font-bold tracking-tight text-center mb-2">
            Welcome to FlyOS
          </h1>
          <p className="text-center text-sm text-zinc-500 mb-10">
            Load Pretty Fly data, validate against the bank, then see what to fix.
          </p>
          <DataLoader />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell
      kpiStrip={
        <KpiStrip
          totalRecoverable={totalRecoverable}
          cashPosition={cashPosition}
          actionCount={leakCount}
          breakdown={breakdown}
        />
      }
    >
      <Suspense fallback={<div className="h-96 animate-pulse rounded-xl bg-[#111]" />}>
        <ActionCenterContent />
      </Suspense>
    </AppShell>
  );
}
