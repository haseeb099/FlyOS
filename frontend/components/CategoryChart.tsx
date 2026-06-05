"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import { fmtGbp } from "@/lib/format";
import type { Breakdown } from "@/lib/types";

const COLORS = ["#fbbf24", "#fb923c", "#60a5fa"];

interface CategoryChartProps {
  breakdown: Breakdown | null;
}

export function CategoryChart({ breakdown }: CategoryChartProps) {
  if (!breakdown) return null;

  const data = [
    { name: "Inventory", value: breakdown.inventory_gbp },
    { name: "Supplier PO", value: breakdown.supplier_gbp },
    { name: "Ad spend", value: breakdown.ads_gbp },
  ].filter((d) => d.value > 0);

  if (data.length === 0) return null;

  return (
    <div className="rounded-xl border border-[#222] bg-[#111] p-4">
      <p className="text-xs text-zinc-500 mb-3 uppercase tracking-wider">Cash by category</p>
      <div className="h-40">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              innerRadius={40}
              outerRadius={60}
              paddingAngle={2}
            >
              {data.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value) => fmtGbp(Number(value ?? 0))}
              contentStyle={{
                background: "#1a1a1a",
                border: "1px solid #333",
                borderRadius: 8,
                fontSize: 12,
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="flex flex-wrap gap-3 mt-2 justify-center">
        {data.map((d, i) => (
          <span key={d.name} className="flex items-center gap-1.5 text-xs text-zinc-400">
            <span
              className="h-2 w-2 rounded-full"
              style={{ background: COLORS[i % COLORS.length] }}
            />
            {d.name}: {fmtGbp(d.value)}
          </span>
        ))}
      </div>
    </div>
  );
}
