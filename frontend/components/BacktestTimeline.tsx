"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { LeakCard } from "@/components/LeakCard";
import { fmtGbp } from "@/lib/format";
import type { BacktestResult } from "@/lib/types";

interface BacktestTimelineProps {
  result: BacktestResult;
}

export function BacktestTimeline({ result }: BacktestTimelineProps) {
  const chartData = [
    {
      name: "Inventory",
      recommended: result.inventory_recovered_gbp ?? 0,
      label: "Stock sold",
    },
    {
      name: "Supplier POs",
      recommended: result.po_recovered_gbp ?? 0,
      label: "Deposits recovered",
    },
    {
      name: "Ad spend",
      recommended: result.ad_saved_gbp ?? 0,
      label: "Spend avoided",
    },
  ].filter((d) => d.recommended > 0);

  return (
    <div className="space-y-8">
      <div className="grid gap-6 lg:grid-cols-2">
        <div>
          <h2 className="text-sm font-medium text-zinc-400 mb-4">
            What we recommended on {result.as_of_date}
          </h2>
          <div className="space-y-4">
            {result.recommendations.length === 0 ? (
              <p className="text-sm text-zinc-500">No leaks flagged on this date.</p>
            ) : (
              result.recommendations.map((leak) => (
                <LeakCard key={leak.id} leak={leak} actionLabel="View detail" />
              ))
            )}
          </div>
        </div>
        <div>
          <h2 className="text-sm font-medium text-zinc-400 mb-4">
            What actually happened (30 days)
          </h2>
          <div className="rounded-xl border border-[#222] bg-[#111] p-6 space-y-4">
            <p className="text-sm text-zinc-300 leading-relaxed">
              {result.actual_outcome_summary}
            </p>
            <ul className="text-xs text-zinc-500 space-y-1 border-t border-[#222] pt-4">
              <li>Inventory recovery: {fmtGbp(result.inventory_recovered_gbp ?? 0)}</li>
              <li>PO deposit recovery: {fmtGbp(result.po_recovered_gbp ?? 0)}</li>
              <li>Ad spend saved: {fmtGbp(result.ad_saved_gbp ?? 0)}</li>
            </ul>
          </div>
        </div>
      </div>

      {chartData.length > 0 && (
        <div className="rounded-xl border border-[#222] bg-[#111] p-6">
          <h3 className="text-sm font-medium text-zinc-400 mb-4">
            Recovery breakdown (30-day forward window)
          </h3>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#222" />
                <XAxis dataKey="name" tick={{ fill: "#71717a", fontSize: 12 }} />
                <YAxis
                  tick={{ fill: "#71717a", fontSize: 12 }}
                  tickFormatter={(v) => `£${(v / 1000).toFixed(0)}k`}
                />
                <Tooltip
                  contentStyle={{
                    background: "#1a1a1a",
                    border: "1px solid #333",
                    borderRadius: 8,
                  }}
                  formatter={(value) => fmtGbp(Number(value ?? 0))}
                />
                <Bar dataKey="recommended" fill="#fbbf24" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      <div className="rounded-xl border border-amber-400/30 bg-amber-400/5 p-8 text-center">
        <p className="text-sm text-zinc-400">Total cash impact if recommendations followed</p>
        <p className="font-mono text-4xl font-bold text-amber-400 mt-2 tabular-nums">
          {fmtGbp(result.estimated_cash_recovered_gbp)}
        </p>
      </div>
    </div>
  );
}
