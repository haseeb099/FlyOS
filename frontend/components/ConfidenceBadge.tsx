import type { Confidence } from "@/lib/types";
import { cn } from "@/lib/utils";

const STYLES: Record<Confidence, string> = {
  high: "bg-green-500/15 text-green-400 border-green-500/30",
  medium: "bg-amber-400/15 text-amber-400 border-amber-400/30",
  low: "bg-zinc-500/15 text-zinc-400 border-zinc-500/30",
};

export function ConfidenceBadge({ confidence }: { confidence: Confidence }) {
  return (
    <span
      className={cn(
        "inline-flex rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide",
        STYLES[confidence]
      )}
    >
      {confidence}
    </span>
  );
}
