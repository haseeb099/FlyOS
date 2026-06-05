"use client";

import { AppShell, MobileNav } from "@/components/AppShell";
import { DataLoader } from "@/components/DataLoader";
import { ReconciliationBadge } from "@/components/ReconciliationBadge";
import { useAppStore } from "@/lib/store";

export default function DataPage() {
  const validationStatus = useAppStore((s) => s.validationStatus);

  return (
    <AppShell>
      <MobileNav />
      <div className="max-w-2xl mx-auto space-y-8 py-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Data & validation</h1>
          <p className="text-sm text-zinc-500 mt-2">
            Load the Pretty Fly CSV pack and run 20 reconciliation checks against
            bank_transactions.csv before using FlyOS.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <ReconciliationBadge />
          <span className="text-xs text-zinc-600">
            Status: {validationStatus}
          </span>
        </div>
        <DataLoader />
      </div>
    </AppShell>
  );
}
