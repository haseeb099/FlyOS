"""Convert pandas leak DataFrames to API CashLeak models."""

from __future__ import annotations

import pandas as pd

from config import TOP_LEAKS_LIMIT
from models import CashLeak


def _confidence(amount: float) -> str:
    if amount >= 1000:
        return "high"
    if amount >= 300:
        return "medium"
    return "low"


def dead_inventory_to_leaks(dead: pd.DataFrame) -> list[CashLeak]:
    leaks: list[CashLeak] = []
    for _, row in dead.iterrows():
        cash = float(row["total_cash_tied_gbp"])
        days = int(row["days_of_stock"]) if row["days_of_stock"] < 900 else 999
        leaks.append(
            CashLeak(
                id=f"inv_{row['variant_id']}",
                category="inventory",
                title=str(row["product_title"]),
                subtitle=f"{row['sku']} · {row['gender_segment']}",
                cash_at_risk_gbp=cash,
                units_or_days=f"{int(row['current_stock_units'])} units",
                recommended_action=str(row["recommended_action"]),
                recoverable_gbp=cash * 0.5,
                confidence=_confidence(cash),  # type: ignore[arg-type]
            )
        )
    return leaks


def late_pos_to_leaks(late: pd.DataFrame) -> list[CashLeak]:
    leaks: list[CashLeak] = []
    for _, row in late.iterrows():
        cash = float(row["recoverable_gbp"])
        leaks.append(
            CashLeak(
                id=f"po_{row['po_id']}",
                category="supplier_po",
                title=f"PO {row['po_id']}",
                subtitle=str(row["supplier_name"]),
                cash_at_risk_gbp=cash,
                units_or_days=f"{int(row['days_overdue'])} days overdue",
                recommended_action=str(row["recommended_action"]),
                recoverable_gbp=cash,
                confidence=_confidence(cash),  # type: ignore[arg-type]
            )
        )
    return leaks


def ad_waste_to_leaks(ad: pd.DataFrame) -> list[CashLeak]:
    leaks: list[CashLeak] = []
    for _, row in ad.iterrows():
        cash = float(row["spend_gbp"])
        leaks.append(
            CashLeak(
                id=f"ad_{row['platform']}_{row['campaign_name']}",
                category="ad_spend",
                title=str(row["campaign_name"]),
                subtitle=str(row["platform"]).title(),
                cash_at_risk_gbp=cash,
                units_or_days=f"{int(row['days_no_conversion'])} days no conversions",
                recommended_action=str(row["recommended_action"]),
                recoverable_gbp=cash,
                confidence=_confidence(cash),  # type: ignore[arg-type]
            )
        )
    return leaks


def build_leak_list(
    dead: pd.DataFrame,
    late: pd.DataFrame,
    ad: pd.DataFrame,
    *,
    limit: int | None = TOP_LEAKS_LIMIT,
) -> list[CashLeak]:
    """Merge and sort leaks by cash at risk."""
    combined = dead_inventory_to_leaks(dead) + late_pos_to_leaks(late) + ad_waste_to_leaks(ad)
    combined.sort(key=lambda leak: leak.cash_at_risk_gbp, reverse=True)
    if limit is not None:
        return combined[:limit]
    return combined
