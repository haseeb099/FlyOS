"use client";

import { useEffect } from "react";

import { getActions, getCashPosition } from "@/lib/api";
import { useAppStore } from "@/lib/store";

/**
 * If the FastAPI server already has validated data in memory, hydrate the UI
 * without making the user click Load again on every page refresh.
 */
export function DataBootstrap() {
  const isDataLoaded = useAppStore((s) => s.isDataLoaded);
  const bootstrapping = useAppStore((s) => s.bootstrapping);
  const setBootstrapping = useAppStore((s) => s.setBootstrapping);
  const setLoaded = useAppStore((s) => s.setLoaded);
  const setValidation = useAppStore((s) => s.setValidation);
  const setCashSummary = useAppStore((s) => s.setCashSummary);
  const setActions = useAppStore((s) => s.setActions);

  useEffect(() => {
    if (isDataLoaded) return;

    let cancelled = false;

    async function hydrateFromApi() {
      setBootstrapping(true);
      try {
        const health = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/health`
        ).then((r) => r.json() as Promise<{ validated: boolean }>);

        if (cancelled || !health.validated) return;

        const [actionsRes, position] = await Promise.all([
          getActions(10),
          getCashPosition(),
        ]);
        if (cancelled) return;

        const breakdown = {
          inventory_gbp: actionsRes.breakdown.inventory_gbp ?? 0,
          supplier_gbp: actionsRes.breakdown.supplier_gbp ?? 0,
          ads_gbp: actionsRes.breakdown.ads_gbp ?? 0,
          item_count: actionsRes.breakdown.item_count ?? actionsRes.action_count,
        };

        setValidation("passed");
        setLoaded(true);
        setActions(
          actionsRes.actions,
          actionsRes.total_liberation_gbp,
          actionsRes.action_count,
          breakdown
        );
        setCashSummary(
          actionsRes.total_liberation_gbp,
          actionsRes.actions.map((a) => a.leak),
          position,
          breakdown
        );
      } catch {
        /* API offline or data not loaded yet — user will use DataLoader */
      } finally {
        if (!cancelled) setBootstrapping(false);
      }
    }

    void hydrateFromApi();
    return () => {
      cancelled = true;
    };
  }, [
    isDataLoaded,
    setBootstrapping,
    setCashSummary,
    setLoaded,
    setValidation,
    setActions,
  ]);

  if (!bootstrapping) return null;

  return (
    <div
      className="fixed bottom-4 right-4 z-50 rounded-lg border border-[#222] bg-[#111] px-4 py-2 text-xs text-zinc-400"
      role="status"
    >
      Syncing with API…
    </div>
  );
}
