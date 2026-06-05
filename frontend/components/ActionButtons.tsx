"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { simulateAction } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import type { ActionItem } from "@/lib/types";

interface ActionButtonsProps {
  action: ActionItem;
  onDraftEmail: () => void;
  onSimulated?: (message: string) => void;
}

export function ActionButtons({ action, onDraftEmail, onSimulated }: ActionButtonsProps) {
  const [loading, setLoading] = useState(false);
  const markActioned = useAppStore((s) => s.markActioned);
  const { leak, action_type } = action;

  const handleSimulate = async () => {
    setLoading(true);
    try {
      const result = await simulateAction(leak.id);
      onSimulated?.(result.message);
    } catch (e) {
      onSimulated?.(e instanceof Error ? e.message : "Simulation failed");
    } finally {
      setLoading(false);
    }
  };

  if (action_type === "draft_email") {
    return (
      <>
        <Button onClick={onDraftEmail}>Draft Email</Button>
        <Button variant="outline" onClick={() => markActioned(leak.id)}>
          Mark done
        </Button>
      </>
    );
  }

  if (action_type === "pause_campaign") {
    return (
      <>
        <Button onClick={handleSimulate} disabled={loading}>
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Pause Campaign"}
        </Button>
        <Button variant="outline" onClick={() => markActioned(leak.id)}>
          Mark done
        </Button>
      </>
    );
  }

  if (action_type === "chase_supplier") {
    return (
      <>
        <Button onClick={handleSimulate} disabled={loading}>
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Chase Supplier"}
        </Button>
        <Button variant="outline" onClick={() => markActioned(leak.id)}>
          Mark done
        </Button>
      </>
    );
  }

  return (
    <Button variant="outline" onClick={() => markActioned(leak.id)}>
      Mark done
    </Button>
  );
}
