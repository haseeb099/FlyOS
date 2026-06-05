"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";

import { ActionButtons } from "@/components/ActionButtons";
import { ConfidenceBadge } from "@/components/ConfidenceBadge";
import { EmailPreview } from "@/components/EmailPreview";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tooltip } from "@/components/ui/tooltip";
import { explainLeak } from "@/lib/api";
import { fmtGbp } from "@/lib/format";
import type { ActionItem } from "@/lib/types";

interface ActionDetailProps {
  action: ActionItem | null;
  onSimulated?: (message: string) => void;
}

export function ActionDetail({ action, onSimulated }: ActionDetailProps) {
  const [explanation, setExplanation] = useState<string | null>(null);
  const [loadingExplain, setLoadingExplain] = useState(false);
  const [showEmail, setShowEmail] = useState(false);

  if (!action) {
    return (
      <div className="flex h-full min-h-[400px] items-center justify-center rounded-xl border border-dashed border-[#333] bg-[#111]/50">
        <div className="text-center px-6">
          <svg
            className="mx-auto h-16 w-16 text-zinc-700"
            viewBox="0 0 64 64"
            fill="none"
            aria-hidden
          >
            <rect x="8" y="12" width="48" height="40" rx="4" stroke="currentColor" strokeWidth="2" />
            <path d="M20 24h24M20 32h16M20 40h20" stroke="currentColor" strokeWidth="2" />
          </svg>
          <p className="mt-4 text-sm text-zinc-500">Select an action from the queue</p>
        </div>
      </div>
    );
  }

  const { leak, evidence } = action;

  const handleExplain = async () => {
    setLoadingExplain(true);
    try {
      const text = await explainLeak(leak.id);
      setExplanation(text);
    } catch {
      setExplanation("Could not load explanation — check API connection.");
    } finally {
      setLoadingExplain(false);
    }
  };

  const emailParams =
    leak.category === "inventory"
      ? {
          leak_id: leak.id,
          variant_title: leak.title,
          units: parseInt(leak.units_or_days, 10) || 0,
          cash_tied: leak.cash_at_risk_gbp,
          sku: leak.subtitle.split("·")[0]?.trim() ?? "",
        }
      : null;

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-zinc-100">{leak.title}</h2>
            <p className="text-sm text-zinc-500 mt-1">{leak.subtitle}</p>
          </div>
          <ConfidenceBadge confidence={leak.confidence} />
        </div>
        <p className="mt-4 text-sm text-zinc-400">{leak.recommended_action}</p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="rounded-xl border border-[#222] bg-[#111] p-4">
          <p className="text-xs text-zinc-500">Cash at risk</p>
          <p className="font-mono text-2xl font-bold text-zinc-200 tabular-nums">
            {fmtGbp(leak.cash_at_risk_gbp)}
          </p>
        </div>
        <div className="rounded-xl border border-amber-400/30 bg-amber-400/5 p-4">
          <p className="text-xs text-zinc-500">Recoverable</p>
          <p className="font-mono text-2xl font-bold text-amber-400 tabular-nums">
            {fmtGbp(leak.recoverable_gbp)}
          </p>
        </div>
      </div>

      <div>
        <h3 className="text-sm font-medium text-zinc-400 mb-3">Evidence</h3>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Metric</TableHead>
              <TableHead>Value</TableHead>
              <TableHead>Lineage</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {evidence.map((row) => (
              <TableRow key={row.metric}>
                <TableCell className="text-zinc-400">{row.metric}</TableCell>
                <TableCell>{row.value}</TableCell>
                <TableCell>
                  <Tooltip
                    content={
                      <span>
                        <strong className="text-zinc-200">Tables:</strong>{" "}
                        {row.source_tables.join(", ")}
                        <br />
                        <strong className="text-zinc-200">Join:</strong> {row.join_path}
                      </span>
                    }
                  >
                    <span className="cursor-help text-amber-400/80 underline decoration-dotted">
                      {row.source_tables.length} tables
                    </span>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <div className="flex flex-wrap gap-3">
        <ActionButtons
          action={action}
          onDraftEmail={() => setShowEmail(true)}
          onSimulated={onSimulated}
        />
        <button
          type="button"
          onClick={handleExplain}
          disabled={loadingExplain}
          className="rounded-lg border border-[#333] px-4 py-2 text-sm text-zinc-400 hover:border-amber-400/40 hover:text-zinc-200"
        >
          {loadingExplain ? (
            <Loader2 className="h-4 w-4 animate-spin inline" />
          ) : (
            "Why this matters"
          )}
        </button>
      </div>

      {explanation && (
        <div className="rounded-xl border border-[#222] bg-[#111] p-4 text-sm text-zinc-300 leading-relaxed">
          {explanation}
        </div>
      )}

      {showEmail && emailParams && (
        <div className="rounded-xl border border-[#222] p-4">
          <h3 className="text-sm font-medium text-zinc-400 mb-4">Email campaign</h3>
          <EmailPreview params={emailParams} />
        </div>
      )}
    </div>
  );
}
