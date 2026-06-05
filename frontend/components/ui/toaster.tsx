"use client";

import { createContext, useCallback, useContext, useState } from "react";

type ToastVariant = "success" | "error" | "default";

interface Toast {
  id: number;
  message: string;
  variant: ToastVariant;
}

interface ToastContextValue {
  toast: (message: string, variant?: ToastVariant) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToasterProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const toast = useCallback((message: string, variant: ToastVariant = "default") => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, variant }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3500);
  }, []);

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={
              t.variant === "success"
                ? "rounded-lg border border-green-500/30 bg-green-500/10 px-4 py-3 text-sm text-green-300 shadow-lg animate-in slide-in-from-right"
                : t.variant === "error"
                  ? "rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300 shadow-lg animate-in slide-in-from-right"
                  : "rounded-lg border border-[#333] bg-[#1a1a1a] px-4 py-3 text-sm text-zinc-200 shadow-lg animate-in slide-in-from-right"
            }
          >
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToasterProvider");
  return ctx;
}
