"use client";

import { cn } from "@/lib/utils";

interface SheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: React.ReactNode;
  title?: string;
}

export function Sheet({ open, onOpenChange, children, title }: SheetProps) {
  if (!open) return null;
  return (
    <>
      <div
        className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
        onClick={() => onOpenChange(false)}
        aria-hidden
      />
      <div
        className={cn(
          "fixed inset-y-0 right-0 z-50 w-full max-w-lg border-l border-[#222] bg-[#0a0a0a] shadow-2xl",
          "animate-in slide-in-from-right duration-300"
        )}
      >
        <div className="flex items-center justify-between border-b border-[#222] px-6 py-4">
          <h2 className="text-lg font-semibold text-zinc-100">{title ?? "Details"}</h2>
          <button
            type="button"
            onClick={() => onOpenChange(false)}
            className="rounded-lg px-2 py-1 text-zinc-400 hover:bg-[#222] hover:text-zinc-200"
            aria-label="Close"
          >
            ✕
          </button>
        </div>
        <div className="overflow-y-auto p-6 max-h-[calc(100vh-4rem)]">{children}</div>
      </div>
    </>
  );
}
