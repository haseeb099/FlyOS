"""Pydantic response models for the FlyOS API."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class CashLeak(BaseModel):
    id: str
    category: Literal["inventory", "supplier_po", "ad_spend"]
    title: str
    subtitle: str
    cash_at_risk_gbp: float
    units_or_days: str
    recommended_action: str
    recoverable_gbp: float
    confidence: Literal["high", "medium", "low"]


class ActionEvidence(BaseModel):
    metric: str
    value: str
    source_tables: list[str]
    join_path: str


class ActionItem(BaseModel):
    rank: int
    leak: CashLeak
    action_type: Literal[
        "draft_email", "pause_campaign", "chase_supplier", "create_po", "mark_done"
    ]
    evidence: list[ActionEvidence] = Field(default_factory=list)


class ActionsResponse(BaseModel):
    total_liberation_gbp: float
    action_count: int
    actions: list[ActionItem]
    breakdown: dict[str, float] = Field(default_factory=dict)
    computed_at: str


class CashPosition(BaseModel):
    bank_balance_gbp: float
    outstanding_payables_gbp: float
    expected_receivables_gbp: float
    net_cash_gbp: float
    as_of_date: str


class CashLeaksResponse(BaseModel):
    total_recoverable_gbp: float
    leaks: list[CashLeak]
    validation_status: str
    computed_at: str
    breakdown: dict[str, float] = Field(default_factory=dict)


class BriefItem(BaseModel):
    id: str
    title: str
    subtitle: str
    amount_gbp: float
    category: Literal["inventory", "supplier_po", "ad_spend"]
    recommended_action: str
    confidence: Literal["high", "medium", "low"]


class ExecutiveBriefing(BaseModel):
    as_of_date: str
    cash_position: CashPosition
    total_liberation_gbp: float
    top_risks: list[BriefItem]
    top_opportunities: list[BriefItem]
    narrative: str | None = None


class BacktestResult(BaseModel):
    as_of_date: str
    recommendations: list[CashLeak]
    actual_outcome_summary: str
    estimated_cash_recovered_gbp: float
    inventory_recovered_gbp: float = 0.0
    po_recovered_gbp: float = 0.0
    ad_saved_gbp: float = 0.0


class BestBacktestDate(BaseModel):
    best_date: str
    estimated_cash_recovered_gbp: float
    summary: str
    candidates: list[dict[str, float | str]] = Field(default_factory=list)


class ReorderSuggestion(BaseModel):
    variant_id: str
    sku: str
    product_title: str
    supplier_name: str
    suggested_qty: int
    unit_cost_gbp: float
    po_value_gbp: float
    days_of_stock: float
    units_sold_30d: float


class SimulateActionRequest(BaseModel):
    leak_id: str


class SimulateActionResponse(BaseModel):
    success: bool
    action: str
    impact_gbp: float
    message: str
    draft: str | None = None


class ValidationFailure(BaseModel):
    rule_number: int
    description: str
    status: Literal["PASS", "FAIL", "SKIP"]
    message: str | None = None


class LoadDataResponse(BaseModel):
    success: bool
    validation_passed: bool
    validation_output: str
    validation_failures: list[ValidationFailure] = Field(default_factory=list)
    files_loaded: list[str]
    message: str


class HealthResponse(BaseModel):
    status: str
    validated: bool
    files_loaded: int


class EmailDraftResponse(BaseModel):
    subject: str
    body: str
    discount_suggestion: str


class LoadDataRequest(BaseModel):
    data_path: str


class GenerateEmailRequest(BaseModel):
    leak_id: str
    variant_title: str
    units: int
    cash_tied: float
    sku: str = ""


def utc_now_iso() -> str:
    """ISO timestamp for API responses."""
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
