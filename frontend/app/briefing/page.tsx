"use client";

import { useEffect } from "react";

import { AppShell, MobileNav } from "@/components/AppShell";
import { BriefingPanel } from "@/components/BriefingPanel";
import { DataLoader } from "@/components/DataLoader";
import { getBriefing } from "@/lib/api";
import { useAppStore } from "@/lib/store";

export default function BriefingPage() {
  const isDataLoaded = useAppStore((s) => s.isDataLoaded);
  const bootstrapping = useAppStore((s) => s.bootstrapping);
  const setBriefing = useAppStore((s) => s.setBriefing);

  useEffect(() => {
    if (!isDataLoaded) return;
    getBriefing()
      .then(setBriefing)
      .catch(() => {});
  }, [isDataLoaded, setBriefing]);

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
      <h1 className="text-2xl font-bold tracking-tight mb-2">Executive Briefing</h1>
      <p className="text-sm text-zinc-500 mb-8">
        Pre-computed risks and opportunities — narrative generated from verified facts only.
      </p>
      <BriefingPanel />
    </AppShell>
  );
}
