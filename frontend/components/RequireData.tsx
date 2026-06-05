"use client";

import { DataLoader } from "@/components/DataLoader";
import { useAppStore } from "@/lib/store";

export function RequireData({ children }: { children: React.ReactNode }) {
  const isDataLoaded = useAppStore((s) => s.isDataLoaded);
  const bootstrapping = useAppStore((s) => s.bootstrapping);

  if (bootstrapping) {
    return (
      <div className="space-y-4 py-8">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="h-28 rounded-xl border border-[#222] bg-[#111] animate-pulse"
          />
        ))}
      </div>
    );
  }

  if (!isDataLoaded) {
    return (
      <div className="py-12">
        <p className="text-center text-sm text-zinc-500 mb-6">
          Load and validate data to continue (or start the API — it auto-loads on
          startup)
        </p>
        <DataLoader />
      </div>
    );
  }

  return <>{children}</>;
}
