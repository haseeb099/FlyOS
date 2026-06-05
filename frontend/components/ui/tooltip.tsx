"use client";

import { cn } from "@/lib/utils";

interface TooltipProps {
  content: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export function Tooltip({ content, children, className }: TooltipProps) {
  return (
    <span className={cn("group relative inline-flex", className)}>
      {children}
      <span
        role="tooltip"
        className="pointer-events-none absolute bottom-full left-1/2 z-50 mb-2 w-64 -translate-x-1/2 rounded-lg border border-[#333] bg-[#1a1a1a] px-3 py-2 text-xs text-zinc-300 opacity-0 shadow-xl transition-opacity group-hover:opacity-100"
      >
        {content}
      </span>
    </span>
  );
}
