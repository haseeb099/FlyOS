"use client";

import { Badge } from "@/components/ui/badge";
import { useAppStore } from "@/lib/store";

export function ReconciliationBadge() {
  const validationStatus = useAppStore((s) => s.validationStatus);

  if (validationStatus === "passed") {
    return <Badge variant="success">✓ Validated</Badge>;
  }
  if (validationStatus === "failed") {
    return <Badge variant="danger">✗ Not Validated</Badge>;
  }
  return <Badge variant="outline">Validation pending</Badge>;
}
