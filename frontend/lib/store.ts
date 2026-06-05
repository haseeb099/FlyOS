import { create } from "zustand";

import type {
  ActionItem,
  Breakdown,
  CashLeak,
  CashPosition,
  ExecutiveBriefing,
  ValidationStatus,
} from "./types";

interface AppStore {
  isDataLoaded: boolean;
  bootstrapping: boolean;
  validationStatus: ValidationStatus;
  cashLeaks: CashLeak[];
  totalRecoverable: number;
  leakCount: number;
  cashPosition: CashPosition | null;
  selectedLeakId: string | null;
  selectedActionId: string | null;
  actionedIds: string[];
  actions: ActionItem[];
  breakdown: Breakdown | null;
  briefing: ExecutiveBriefing | null;
  setBootstrapping: (v: boolean) => void;
  setLoaded: (loaded: boolean) => void;
  setValidation: (status: ValidationStatus) => void;
  setCashSummary: (
    total: number,
    leaks: CashLeak[],
    position?: CashPosition | null,
    breakdown?: Breakdown | null
  ) => void;
  setActions: (
    actions: ActionItem[],
    total: number,
    count: number,
    breakdown: Breakdown
  ) => void;
  setSelectedLeak: (id: string | null) => void;
  setSelectedAction: (id: string | null) => void;
  markActioned: (id: string) => void;
  setBriefing: (briefing: ExecutiveBriefing | null) => void;
  reset: () => void;
}

const initialState = {
  isDataLoaded: false,
  bootstrapping: false,
  validationStatus: "pending" as ValidationStatus,
  cashLeaks: [] as CashLeak[],
  totalRecoverable: 0,
  leakCount: 0,
  cashPosition: null as CashPosition | null,
  selectedLeakId: null as string | null,
  selectedActionId: null as string | null,
  actionedIds: [] as string[],
  actions: [] as ActionItem[],
  breakdown: null as Breakdown | null,
  briefing: null as ExecutiveBriefing | null,
};

export const useAppStore = create<AppStore>((set) => ({
  ...initialState,
  setBootstrapping: (bootstrapping) => set({ bootstrapping }),
  setLoaded: (loaded) => set({ isDataLoaded: loaded }),
  setValidation: (status) => set({ validationStatus: status }),
  setCashSummary: (total, leaks, position = null, breakdown = null) =>
    set({
      totalRecoverable: total,
      cashLeaks: leaks,
      leakCount: leaks.length,
      cashPosition: position,
      breakdown,
    }),
  setActions: (actions, total, count, breakdown) =>
    set({
      actions,
      totalRecoverable: total,
      leakCount: count,
      breakdown,
      selectedActionId: actions[0]?.leak.id ?? null,
    }),
  setSelectedLeak: (id) => set({ selectedLeakId: id }),
  setSelectedAction: (id) => set({ selectedActionId: id }),
  markActioned: (id) =>
    set((s) => ({
      actionedIds: s.actionedIds.includes(id)
        ? s.actionedIds
        : [...s.actionedIds, id],
    })),
  setBriefing: (briefing) => set({ briefing }),
  reset: () => set(initialState),
}));
