"use client";

import { Suspense, useMemo } from "react";
import { useSearchParams } from "next/navigation";

import { AppShell, MobileNav } from "@/components/AppShell";
import { DataLoader } from "@/components/DataLoader";
import { EmailPreview } from "@/components/EmailPreview";
import { useAppStore } from "@/lib/store";
import type { EmailParams } from "@/lib/types";

function EmailContent() {
  const searchParams = useSearchParams();
  const cashLeaks = useAppStore((s) => s.cashLeaks);
  const selectedLeakId = useAppStore((s) => s.selectedLeakId);
  const setSelectedLeak = useAppStore((s) => s.setSelectedLeak);

  const inventoryLeaks = useMemo(
    () => cashLeaks.filter((l) => l.category === "inventory"),
    [cashLeaks]
  );

  const queryLeak = searchParams.get("leak");
  const activeId = queryLeak ?? selectedLeakId ?? inventoryLeaks[0]?.id ?? "";

  const activeLeak = inventoryLeaks.find((l) => l.id === activeId) ?? inventoryLeaks[0];

  const emailParams: EmailParams | null = activeLeak
    ? {
        leak_id: activeLeak.id,
        variant_title: activeLeak.title,
        units: parseInt(activeLeak.units_or_days.match(/\d+/)?.[0] ?? "0", 10),
        cash_tied: activeLeak.cash_at_risk_gbp,
        sku: activeLeak.subtitle.split("·")[0]?.trim() ?? "",
      }
    : null;

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <label className="text-xs text-zinc-500 block mb-1">Dead stock item</label>
        <select
          value={activeLeak?.id ?? ""}
          onChange={(e) => setSelectedLeak(e.target.value)}
          className="w-full rounded-lg border border-[#222] bg-[#111] px-4 py-2 text-sm text-zinc-100"
        >
          {inventoryLeaks.length === 0 ? (
            <option value="">No inventory leaks loaded</option>
          ) : (
            inventoryLeaks.map((leak) => (
              <option key={leak.id} value={leak.id}>
                {leak.title} — {leak.units_or_days}
              </option>
            ))
          )}
        </select>
      </div>
      <EmailPreview params={emailParams} />
    </div>
  );
}

export default function EmailPage() {
  const isDataLoaded = useAppStore((s) => s.isDataLoaded);
  const bootstrapping = useAppStore((s) => s.bootstrapping);

  if (bootstrapping) {
    return (
      <AppShell>
        <div className="py-24 text-center text-zinc-500">Syncing…</div>
      </AppShell>
    );
  }

  if (!isDataLoaded) {
    return (
      <AppShell>
        <div className="max-w-xl mx-auto py-12">
          <DataLoader />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <MobileNav />
      <h1 className="text-2xl font-bold tracking-tight mb-2">Email draft</h1>
      <p className="text-sm text-zinc-500 mb-8">
        Generate Klaviyo-ready copy to clear dead stock (Claude narrates; numbers from pandas).
      </p>
      <Suspense fallback={<div className="h-40 animate-pulse rounded-xl bg-[#111]" />}>
        <EmailContent />
      </Suspense>
    </AppShell>
  );
}
