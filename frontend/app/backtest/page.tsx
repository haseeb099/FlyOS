"use client";

import { useState } from "react";

import { AppShell, MobileNav } from "@/components/AppShell";
import { BacktestTimeline } from "@/components/BacktestTimeline";
import { DataLoader } from "@/components/DataLoader";
import { Button } from "@/components/ui/button";
import { getBestBacktestDate, runBacktest } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import type { BacktestResult } from "@/lib/types";

function BacktestContent() {
  const [date, setDate] = useState("2026-02-01");
  const [loading, setLoading] = useState(false);
  const [bestLoading, setBestLoading] = useState(false);
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await runBacktest(date);
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Backtest failed");
    } finally {
      setLoading(false);
    }
  };

  const handleBestDate = async () => {
    setBestLoading(true);
    setError(null);
    try {
      const best = await getBestBacktestDate();
      setDate(best.best_date);
      const data = await runBacktest(best.best_date);
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not find best date");
    } finally {
      setBestLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end gap-4">
        <div>
          <label className="text-xs text-zinc-500 block mb-1">As-of date</label>
          <input
            type="date"
            min="2024-06-01"
            max="2026-05-31"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="rounded-lg border border-[#222] bg-[#111] px-4 py-2 text-sm text-zinc-100"
          />
        </div>
        <Button onClick={handleRun} disabled={loading}>
          {loading ? "Running…" : "Run backtest"}
        </Button>
        <Button variant="outline" onClick={handleBestDate} disabled={bestLoading}>
          {bestLoading ? "Scanning…" : "Best demo date"}
        </Button>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {loading && (
        <div className="h-48 rounded-xl border border-[#222] bg-[#111] animate-pulse" />
      )}

      {result && !loading && <BacktestTimeline result={result} />}
    </div>
  );
}

export default function BacktestPage() {
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
      <h1 className="text-2xl font-bold tracking-tight mb-2">Backtest</h1>
      <p className="text-sm text-zinc-500 mb-8">
        See what FlyOS would have flagged — and what happened in the next 30 days.
      </p>
      <BacktestContent />
    </AppShell>
  );
}
