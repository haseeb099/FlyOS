"""Ranked action recommendations with evidence for the FlyOS Action Center."""

from __future__ import annotations

from datetime import date
from typing import Any, Literal

import pandas as pd

from cash_engine import (
    compute_cash_liberation_total,
    find_ad_waste,
    find_dead_inventory,
    find_late_pos,
    find_reorder_candidates,
    find_slow_stock,
)
from config import DATASET_TODAY
from leak_mapper import build_leak_list
from models import ActionEvidence, ActionItem, CashLeak

ActionType = Literal[
    "draft_email", "pause_campaign", "chase_supplier", "create_po", "mark_done"
]


def _action_type_for_leak(leak: CashLeak) -> ActionType:
    if leak.category == "inventory":
        return "draft_email"
    if leak.category == "supplier_po":
        return "chase_supplier"
    if leak.category == "ad_spend":
        return "pause_campaign"
    return "mark_done"


def _evidence_for_leak(leak: CashLeak, row: pd.Series | None = None) -> list[ActionEvidence]:
    """Build structured evidence rows for UI tooltips."""
    if leak.category == "inventory":
        return [
            ActionEvidence(
                metric="Cash tied (landed cost)",
                value=f"£{leak.cash_at_risk_gbp:,.0f}",
                source_tables=["inventory_movements", "po_line_items", "purchase_orders"],
                join_path="variant_id → landed cost × on-hand units",
            ),
            ActionEvidence(
                metric="Units on hand",
                value=leak.units_or_days,
                source_tables=["inventory_movements"],
                join_path="SUM(quantity_delta) through as_of_date",
            ),
            ActionEvidence(
                metric="Recoverable (50% markdown)",
                value=f"£{leak.recoverable_gbp:,.0f}",
                source_tables=["variants", "products"],
                join_path="variant_id → product metadata",
            ),
        ]
    if leak.category == "supplier_po":
        return [
            ActionEvidence(
                metric="Days overdue",
                value=leak.units_or_days,
                source_tables=["purchase_orders", "suppliers"],
                join_path="expected_delivery vs as_of_date",
            ),
            ActionEvidence(
                metric="Recoverable deposit/balance",
                value=f"£{leak.recoverable_gbp:,.0f}",
                source_tables=["purchase_orders", "bank_transactions"],
                join_path="PO terms → outstanding payment",
            ),
        ]
    return [
        ActionEvidence(
            metric="Ad spend (14d)",
            value=f"£{leak.cash_at_risk_gbp:,.0f}",
            source_tables=["google_ads_daily", "meta_ads_daily", "orders"],
            join_path="campaign_name → UTM attribution → revenue",
        ),
        ActionEvidence(
            metric="Recoverable if paused",
            value=f"£{leak.recoverable_gbp:,.0f}",
            source_tables=["google_ads_daily", "meta_ads_daily"],
            join_path="SUM(spend_gbp) last 14 days",
        ),
    ]


def _leak_lookup_rows(
    dead: pd.DataFrame,
    late: pd.DataFrame,
    ad: pd.DataFrame,
    slow: pd.DataFrame,
) -> dict[str, pd.Series]:
    lookup: dict[str, pd.Series] = {}
    for _, row in dead.iterrows():
        lookup[f"inv_{row['variant_id']}"] = row
    for _, row in slow.iterrows():
        lookup[f"slow_{row['variant_id']}"] = row
    for _, row in late.iterrows():
        lookup[f"po_{row['po_id']}"] = row
    for _, row in ad.iterrows():
        lookup[f"ad_{row['platform']}_{row['campaign_name']}"] = row
    return lookup


def build_action_list(
    dfs: dict[str, pd.DataFrame],
    as_of_date: date = DATASET_TODAY,
    *,
    limit: int = 5,
) -> tuple[list[ActionItem], dict[str, float | int]]:
    """
    Rank top actions by recoverable_gbp with evidence and CTA metadata.

    Returns actions and full liberation breakdown for KPI strip.
    """
    suppliers = dfs.get("suppliers")
    dead = find_dead_inventory(dfs, as_of_date)
    slow = find_slow_stock(dfs, as_of_date)
    late = find_late_pos(dfs["purchase_orders"], as_of_date, suppliers)
    ad = find_ad_waste(
        dfs["google_ads_daily"],
        dfs["meta_ads_daily"],
        dfs["orders"],
        as_of_date,
        window_days=14,
    )

    totals = compute_cash_liberation_total(dead, late, ad)
    leaks = build_leak_list(dead, late, ad, limit=None)

    # Add slow stock as medium-confidence inventory actions
    for _, row in slow.iterrows():
        cash = float(row["total_cash_tied_gbp"])
        days = int(row["days_of_stock"]) if row["days_of_stock"] < 900 else 999
        leaks.append(
            CashLeak(
                id=f"slow_{row['variant_id']}",
                category="inventory",
                title=str(row["product_title"]),
                subtitle=f"{row['sku']} · slow mover",
                cash_at_risk_gbp=cash,
                units_or_days=f"{int(row['current_stock_units'])} units · {days}d cover",
                recommended_action=str(row["recommended_action"]),
                recoverable_gbp=cash * 0.35,
                confidence="medium",
            )
        )

    leaks.sort(key=lambda leak: leak.recoverable_gbp, reverse=True)
    row_lookup = _leak_lookup_rows(dead, late, ad, slow)

    actions: list[ActionItem] = []
    for rank, leak in enumerate(leaks[:limit], start=1):
        actions.append(
            ActionItem(
                rank=rank,
                leak=leak,
                action_type=_action_type_for_leak(leak),
                evidence=_evidence_for_leak(leak, row_lookup.get(leak.id)),
            )
        )

    return actions, totals


def simulate_action(
    leak_id: str,
    dfs: dict[str, pd.DataFrame],
    as_of_date: date = DATASET_TODAY,
) -> dict[str, Any]:
    """Demo-only impact estimate for pause/chase/mark actions."""
    suppliers = dfs.get("suppliers")
    dead = find_dead_inventory(dfs, as_of_date)
    slow = find_slow_stock(dfs, as_of_date)
    late = find_late_pos(dfs["purchase_orders"], as_of_date, suppliers)
    ad = find_ad_waste(
        dfs["google_ads_daily"],
        dfs["meta_ads_daily"],
        dfs["orders"],
        as_of_date,
        window_days=14,
    )
    leaks = build_leak_list(dead, late, ad, limit=None)
    for _, row in slow.iterrows():
        cash = float(row["total_cash_tied_gbp"])
        leaks.append(
            CashLeak(
                id=f"slow_{row['variant_id']}",
                category="inventory",
                title=str(row["product_title"]),
                subtitle=str(row["sku"]),
                cash_at_risk_gbp=cash,
                units_or_days=f"{int(row['current_stock_units'])} units",
                recommended_action=str(row["recommended_action"]),
                recoverable_gbp=cash * 0.35,
                confidence="medium",
            )
        )

    leak = next((l for l in leaks if l.id == leak_id), None)
    if leak is None:
        return {
            "success": False,
            "action": "unknown",
            "impact_gbp": 0.0,
            "message": f"Unknown action id: {leak_id}",
            "draft": None,
        }

    if leak.category == "ad_spend":
        return {
            "success": True,
            "action": "pause_campaign",
            "impact_gbp": leak.recoverable_gbp,
            "message": (
                f"Pausing {leak.title} saves an estimated "
                f"£{leak.recoverable_gbp:,.0f} over the next 14 days."
            ),
            "draft": f"Hi team — please pause Meta/Google campaign '{leak.title}' immediately. "
            f"£{leak.cash_at_risk_gbp:,.0f} spent with negative ROI in the last 14 days.",
        }
    if leak.category == "supplier_po":
        return {
            "success": True,
            "action": "chase_supplier",
            "impact_gbp": leak.recoverable_gbp,
            "message": (
                f"Chasing {leak.subtitle} could recover "
                f"£{leak.recoverable_gbp:,.0f} in deposit or balance."
            ),
            "draft": (
                f"Hi {leak.subtitle} — PO {leak.title} is {leak.units_or_days}. "
                f"Please confirm delivery date or agree cancellation terms."
            ),
        }
    return {
        "success": True,
        "action": "draft_email",
        "impact_gbp": leak.recoverable_gbp,
        "message": f"Email campaign could recover ~£{leak.recoverable_gbp:,.0f} at 50% clearance.",
        "draft": None,
    }


def build_briefing_items(
    dfs: dict[str, pd.DataFrame],
    as_of_date: date = DATASET_TODAY,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Top 3 risks (cash at risk) and top 3 opportunities (recoverable, high confidence)."""
    suppliers = dfs.get("suppliers")
    dead = find_dead_inventory(dfs, as_of_date)
    late = find_late_pos(dfs["purchase_orders"], as_of_date, suppliers)
    ad = find_ad_waste(
        dfs["google_ads_daily"],
        dfs["meta_ads_daily"],
        dfs["orders"],
        as_of_date,
        window_days=14,
    )
    leaks = build_leak_list(dead, late, ad, limit=None)

    risks = sorted(leaks, key=lambda l: l.cash_at_risk_gbp, reverse=True)[:3]
    opportunities = sorted(
        [l for l in leaks if l.confidence == "high"],
        key=lambda l: l.recoverable_gbp,
        reverse=True,
    )[:3]

    def _to_brief(leak: CashLeak, kind: str) -> dict[str, Any]:
        amount = leak.cash_at_risk_gbp if kind == "risk" else leak.recoverable_gbp
        return {
            "id": leak.id,
            "title": leak.title,
            "subtitle": leak.subtitle,
            "amount_gbp": amount,
            "category": leak.category,
            "recommended_action": leak.recommended_action,
            "confidence": leak.confidence,
        }

    return (
        [_to_brief(l, "risk") for l in risks],
        [_to_brief(l, "opp") for l in opportunities],
    )
