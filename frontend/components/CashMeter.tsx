"use client";

import { useEffect, useState } from "react";

import { ReconciliationBadge } from "@/components/ReconciliationBadge";
import { fmtGbp } from "@/lib/format";

interface CashMeterProps {
  totalGbp: number;
}

export function CashMeter({ totalGbp }: CashMeterProps) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    const duration = 2000;
    const start = performance.now();
    const from = 0;
    const to = totalGbp;

    const tick = (now: number) => {
      const t = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplay(from + (to - from) * eased);
      if (t < 1) requestAnimationFrame(tick);
    };

    requestAnimationFrame(tick);
  }, [totalGbp]);

  return (
    <div className="text-center py-8">
      <p className="text-xs uppercase tracking-widest text-zinc-500 mb-2">
        Cash you can free
      </p>
      <p className="font-mono text-6xl font-bold text-amber-400 tabular-nums">
        {fmtGbp(display)}
      </p>
      <p className="text-sm text-zinc-400 mt-2">recoverable by end of June</p>
      <div className="mt-4 flex justify-center">
        <ReconciliationBadge />
      </div>
    </div>
  );
}
