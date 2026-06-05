export type LeakCategory = "inventory" | "supplier_po" | "ad_spend";
export type Confidence = "high" | "medium" | "low";
export type ValidationStatus = "pending" | "passed" | "failed";
export type ActionType =
  | "draft_email"
  | "pause_campaign"
  | "chase_supplier"
  | "create_po"
  | "mark_done";

export interface CashLeak {
  id: string;
  category: LeakCategory;
  title: string;
  subtitle: string;
  cash_at_risk_gbp: number;
  units_or_days: string;
  recommended_action: string;
  recoverable_gbp: number;
  confidence: Confidence;
}

export interface ActionEvidence {
  metric: string;
  value: string;
  source_tables: string[];
  join_path: string;
}

export interface ActionItem {
  rank: number;
  leak: CashLeak;
  action_type: ActionType;
  evidence: ActionEvidence[];
}

export interface ActionsResponse {
  total_liberation_gbp: number;
  action_count: number;
  actions: ActionItem[];
  breakdown: Record<string, number>;
  computed_at: string;
}

export interface CashLeaksResponse {
  total_recoverable_gbp: number;
  leaks: CashLeak[];
  validation_status: string;
  computed_at: string;
  breakdown?: Record<string, number>;
}

export interface CashPosition {
  bank_balance_gbp: number;
  outstanding_payables_gbp: number;
  expected_receivables_gbp: number;
  net_cash_gbp: number;
  as_of_date: string;
}

export interface BriefItem {
  id: string;
  title: string;
  subtitle: string;
  amount_gbp: number;
  category: LeakCategory;
  recommended_action: string;
  confidence: Confidence;
}

export interface ExecutiveBriefing {
  as_of_date: string;
  cash_position: CashPosition;
  total_liberation_gbp: number;
  top_risks: BriefItem[];
  top_opportunities: BriefItem[];
  narrative?: string | null;
}

export interface BacktestResult {
  as_of_date: string;
  recommendations: CashLeak[];
  actual_outcome_summary: string;
  estimated_cash_recovered_gbp: number;
  inventory_recovered_gbp?: number;
  po_recovered_gbp?: number;
  ad_saved_gbp?: number;
}

export interface BestBacktestDate {
  best_date: string;
  estimated_cash_recovered_gbp: number;
  summary: string;
  candidates?: Array<{ date: string; estimated_cash_recovered_gbp: number; summary: string }>;
}

export interface ValidationFailure {
  rule_number: number;
  description: string;
  status: "PASS" | "FAIL" | "SKIP";
  message?: string | null;
}

export interface LoadDataResponse {
  success: boolean;
  validation_passed: boolean;
  validation_output: string;
  validation_failures?: ValidationFailure[];
  files_loaded: string[];
  message: string;
}

export interface HealthResponse {
  status: string;
  validated: boolean;
  files_loaded: number;
}

export interface EmailParams {
  leak_id: string;
  variant_title: string;
  units: number;
  cash_tied: number;
  sku?: string;
}

export interface SimulateActionResponse {
  success: boolean;
  action: string;
  impact_gbp: number;
  message: string;
  draft?: string | null;
}

export interface Breakdown {
  inventory_gbp: number;
  supplier_gbp: number;
  ads_gbp: number;
  item_count: number;
}
