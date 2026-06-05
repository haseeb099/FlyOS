"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getActions, getCashPosition, loadData } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import type { ValidationFailure } from "@/lib/types";

const DEFAULT_PATH = "../pretty_fly_data_pack/data";

export function DataLoader() {
  const [path, setPath] = useState(DEFAULT_PATH);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [failOutput, setFailOutput] = useState<string | null>(null);
  const [failures, setFailures] = useState<ValidationFailure[]>([]);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const setLoaded = useAppStore((s) => s.setLoaded);
  const setValidation = useAppStore((s) => s.setValidation);
  const setCashSummary = useAppStore((s) => s.setCashSummary);
  const setActions = useAppStore((s) => s.setActions);

  const handleLoad = async () => {
    setLoading(true);
    setError(null);
    setFailOutput(null);
    setFailures([]);
    setSuccessMsg(null);
    setValidation("pending");

    try {
      const result = await loadData(path);
      if (!result.validation_passed) {
        setValidation("failed");
        setFailOutput(result.validation_output);
        setFailures(result.validation_failures ?? []);
        setError("Reconciliation checks failed. Fix the data or path and try again.");
        return;
      }

      setValidation("passed");
      setLoaded(true);

      const [actionsRes, position] = await Promise.all([
        getActions(10),
        getCashPosition(),
      ]);

      const breakdown = {
        inventory_gbp: actionsRes.breakdown.inventory_gbp ?? 0,
        supplier_gbp: actionsRes.breakdown.supplier_gbp ?? 0,
        ads_gbp: actionsRes.breakdown.ads_gbp ?? 0,
        item_count: actionsRes.breakdown.item_count ?? actionsRes.action_count,
      };

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
      setSuccessMsg(
        `All checks passed. ${result.files_loaded.length} files loaded.`
      );
    } catch (e) {
      setValidation("failed");
      setError(e instanceof Error ? e.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="max-w-xl mx-auto">
      <CardHeader>
        <CardTitle>Load Pretty Fly data</CardTitle>
        <p className="text-sm text-zinc-400">
          Point at the hackathon CSV folder. FlyOS runs 20 reconciliation checks before
          showing actions.
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        <input
          type="text"
          value={path}
          onChange={(e) => setPath(e.target.value)}
          placeholder="../pretty_fly_data_pack/data"
          className="w-full rounded-lg border border-[#222] bg-[#0a0a0a] px-4 py-3 text-sm text-zinc-100 placeholder:text-zinc-600 focus:border-amber-400/50 focus:outline-none"
        />
        <Button
          className="w-full"
          disabled={loading || !path.trim()}
          onClick={handleLoad}
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Running 20 reconciliation checks…
            </>
          ) : (
            "Load & Validate"
          )}
        </Button>

        {successMsg && (
          <div className="rounded-lg border border-green-500/30 bg-green-500/10 p-4 text-sm text-green-300">
            ✓ {successMsg}
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
            <p className="font-medium">✗ {error}</p>
            {failures.length > 0 ? (
              <ul className="mt-3 space-y-2 text-xs">
                {failures.map((f) => (
                  <li key={f.rule_number} className="border-l-2 border-red-500/50 pl-2">
                    <strong>Rule {f.rule_number}:</strong> {f.description}
                    {f.message && (
                      <p className="text-red-200/70 mt-0.5 whitespace-pre-wrap">{f.message}</p>
                    )}
                  </li>
                ))}
              </ul>
            ) : (
              failOutput && (
                <pre className="mt-2 max-h-40 overflow-auto text-xs text-red-200/80 whitespace-pre-wrap">
                  {failOutput.slice(0, 1200)}
                </pre>
              )
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
