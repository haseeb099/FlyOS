"""
Cash leak computation for Pretty Fly — pandas only, no LLM.

All monetary values are computed here and passed to Claude for narration only.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import numpy as np
import pandas as pd

from config import DATASET_TODAY

DEAD_STOCK_MIN_DAYS = 45
DEAD_STOCK_MAX_WEEKLY = 2
DEAD_STOCK_MIN_UNITS = 10
SLOW_STOCK_MAX_DAILY = 1.0
SLOW_STOCK_MIN_DAYS = 45
REORDER_MAX_DAYS_STOCK = 14
INFINITE_DAYS_OF_STOCK = 999
DEFAULT_DEPOSIT_FRACTION = 0.5
DELIVERED_STATUSES = frozenset({"received", "delivered"})


def _as_timestamp(d: date) -> pd.Timestamp:
    return pd.Timestamp(d)


def compute_landed_cost(
    po_line_items: pd.DataFrame,
    purchase_orders: pd.DataFrame,
    as_of_date: date = DATASET_TODAY,
) -> pd.DataFrame:
    """
    Average landed cost per variant from POs delivered on or before as_of_date.

    Returns:
        DataFrame with columns [variant_id, avg_landed_cost_gbp].
    """
    as_of = _as_timestamp(as_of_date)
    po = purchase_orders.copy()
    po["actual_delivery"] = pd.to_datetime(po["actual_delivery"], errors="coerce")
    delivered = po[po["actual_delivery"].notna() & (po["actual_delivery"] <= as_of)]

    merged = po_line_items.merge(
        delivered[["po_id", "actual_delivery"]],
        on="po_id",
        how="inner",
    )
    cost_col = (
        "landed_cost_per_unit_gbp"
        if "landed_cost_per_unit_gbp" in merged.columns
        else "unit_cost"
    )
    return (
        merged.groupby("variant_id", as_index=False)[cost_col]
        .mean()
        .rename(columns={cost_col: "avg_landed_cost_gbp"})
    )


def compute_current_stock(
    inventory_movements: pd.DataFrame,
    as_of_date: date = DATASET_TODAY,
) -> pd.DataFrame:
    """
    Sum inventory movement deltas through as_of_date.

    Returns:
        DataFrame with columns [variant_id, current_stock_units].
    """
    as_of = _as_timestamp(as_of_date)
    moves = inventory_movements.copy()
    moves["date"] = pd.to_datetime(moves["date"], errors="coerce")
    moves = moves[moves["date"] <= as_of]
    qty_col = "quantity_delta" if "quantity_delta" in moves.columns else "quantity_change"
    return (
        moves.groupby("variant_id", as_index=False)[qty_col]
        .sum()
        .rename(columns={qty_col: "current_stock_units"})
    )


def compute_sales_velocity(
    line_items: pd.DataFrame,
    orders: pd.DataFrame,
    as_of_date: date = DATASET_TODAY,
    window_days: int = 30,
) -> pd.DataFrame:
    """
    Units sold in the trailing window and implied days of stock.

    Returns:
        DataFrame with columns [variant_id, units_sold, avg_daily_sales, days_of_stock].
    """
    as_of = _as_timestamp(as_of_date)
    cutoff = as_of - timedelta(days=window_days)

    sold = (
        line_items.merge(orders[["order_id", "created_at"]], on="order_id", how="inner")
        .assign(created_at=lambda df: pd.to_datetime(df["created_at"], errors="coerce"))
        .query("created_at >= @cutoff and created_at <= @as_of")
        .groupby("variant_id", as_index=False)["quantity"]
        .sum()
        .rename(columns={"quantity": "units_sold"})
    )
    sold["avg_daily_sales"] = sold["units_sold"] / float(window_days)
    return sold


def _attach_days_of_stock(
    stock: pd.DataFrame,
    velocity: pd.DataFrame,
    window_days: int,
) -> pd.DataFrame:
    merged = stock.merge(velocity, on="variant_id", how="left")
    merged["units_sold"] = merged["units_sold"].fillna(0)
    merged["avg_daily_sales"] = merged["avg_daily_sales"].fillna(0)

    def _days(row: pd.Series) -> float:
        if row["current_stock_units"] <= 0:
            return 0.0
        if row["avg_daily_sales"] <= 0:
            return float(INFINITE_DAYS_OF_STOCK)
        return float(row["current_stock_units"] / row["avg_daily_sales"])

    merged["days_of_stock"] = merged.apply(_days, axis=1)
    merged[f"units_sold_last_{window_days}d"] = merged["units_sold"]
    return merged


def find_dead_inventory(
    dfs: dict[str, pd.DataFrame],
    as_of_date: date = DATASET_TODAY,
) -> pd.DataFrame:
    """
    Rank slow-moving stock by cash tied up (landed cost × on-hand units).

    Criteria: days_of_stock > 45 AND (fewer than 2 units sold in 7d OR
    zero sales in 14d with stock > 10).
    """
    landed = compute_landed_cost(
        dfs["po_line_items"], dfs["purchase_orders"], as_of_date
    )
    stock = compute_current_stock(dfs["inventory_movements"], as_of_date)
    velocity_30 = compute_sales_velocity(
        dfs["line_items"], dfs["orders"], as_of_date, window_days=30
    )
    velocity_7 = compute_sales_velocity(
        dfs["line_items"], dfs["orders"], as_of_date, window_days=7
    ).rename(columns={"units_sold": "units_sold_last_7d"})[
        ["variant_id", "units_sold_last_7d"]
    ]

    base = _attach_days_of_stock(stock, velocity_30, window_days=30)
    base = base.merge(landed, on="variant_id", how="inner")
    base = base.merge(velocity_7, on="variant_id", how="left")
    base["units_sold_last_7d"] = base["units_sold_last_7d"].fillna(0).astype(int)

    base["total_cash_tied_gbp"] = (
        base["current_stock_units"].clip(lower=0) * base["avg_landed_cost_gbp"]
    )

    velocity_14 = compute_sales_velocity(
        dfs["line_items"], dfs["orders"], as_of_date, window_days=14
    ).rename(columns={"units_sold": "units_sold_last_14d"})[
        ["variant_id", "units_sold_last_14d"]
    ]
    base = base.merge(velocity_14, on="variant_id", how="left")
    base["units_sold_last_14d"] = base["units_sold_last_14d"].fillna(0).astype(int)

    no_sales_14d = base["units_sold_last_14d"] == 0
    classic_dead = (base["days_of_stock"] > DEAD_STOCK_MIN_DAYS) & (
        base["units_sold_last_7d"] < DEAD_STOCK_MAX_WEEKLY
    )
    extended_dead = no_sales_14d & (base["current_stock_units"] > DEAD_STOCK_MIN_UNITS)

    dead = base[
        (base["current_stock_units"] > 0) & (classic_dead | extended_dead)
    ].copy()

    meta = dfs["variants"].merge(
        dfs["products"][["product_id", "title", "gender_segment"]],
        on="product_id",
        how="left",
    )[["variant_id", "sku", "title", "gender_segment"]]

    dead = dead.merge(meta, on="variant_id", how="left")
    dead = dead.rename(columns={"title": "product_title"})
    dead["recommended_action"] = np.where(
        dead["units_sold_last_7d"] == 0,
        "Bundle & Save email — zero sales last 7 days",
        "20% markdown — under 2 units/week",
    )

    cols = [
        "variant_id",
        "sku",
        "product_title",
        "gender_segment",
        "current_stock_units",
        "avg_landed_cost_gbp",
        "total_cash_tied_gbp",
        "days_of_stock",
        "units_sold_last_7d",
        "recommended_action",
    ]
    return dead[cols].sort_values("total_cash_tied_gbp", ascending=False)


def find_late_pos(
    purchase_orders: pd.DataFrame,
    as_of_date: date = DATASET_TODAY,
    suppliers: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    POs past expected delivery that are not fully received as of as_of_date.

    Recoverable amount estimates outstanding deposit (50% default terms).
    """
    as_of = _as_timestamp(as_of_date)
    po = purchase_orders.copy()
    po["expected_delivery"] = pd.to_datetime(po["expected_delivery"], errors="coerce")
    po["actual_delivery"] = pd.to_datetime(po["actual_delivery"], errors="coerce")
    po["balance_paid_at"] = pd.to_datetime(po["balance_paid_at"], errors="coerce")

    late_mask = (po["expected_delivery"] < as_of) & (
        po["actual_delivery"].isna()
        | (po["actual_delivery"] > as_of)
        | (~po["status"].str.lower().isin(DELIVERED_STATUSES))
    )
    late = po[late_mask].copy()
    if late.empty:
        return pd.DataFrame(
            columns=[
                "po_id",
                "supplier_name",
                "deposit_paid_gbp",
                "balance_gbp",
                "days_overdue",
                "recoverable_gbp",
                "recommended_action",
            ]
        )

    late["days_overdue"] = (as_of - late["expected_delivery"]).dt.days
    late["deposit_paid_gbp"] = late["total_cost_gbp"] * DEFAULT_DEPOSIT_FRACTION
    balance_unpaid = late["balance_paid_at"].isna() | (late["balance_paid_at"] > as_of)
    late["balance_gbp"] = np.where(
        balance_unpaid,
        late["total_cost_gbp"] * (1 - DEFAULT_DEPOSIT_FRACTION),
        0.0,
    )
    late["recoverable_gbp"] = np.where(
        balance_unpaid,
        late["deposit_paid_gbp"],
        late["balance_gbp"],
    )
    late["recommended_action"] = "Chase supplier or cancel PO — delivery overdue"

    if suppliers is not None and not suppliers.empty:
        late = late.merge(
            suppliers[["supplier_id", "name"]].rename(columns={"name": "supplier_name"}),
            on="supplier_id",
            how="left",
        )
    else:
        late["supplier_name"] = late["supplier_id"]

    return late[
        [
            "po_id",
            "supplier_name",
            "deposit_paid_gbp",
            "balance_gbp",
            "days_overdue",
            "recoverable_gbp",
            "recommended_action",
        ]
    ].sort_values("days_overdue", ascending=False)


def find_slow_stock(
    dfs: dict[str, pd.DataFrame],
    as_of_date: date = DATASET_TODAY,
) -> pd.DataFrame:
    """
    Medium-confidence slow movers: under 1 unit/day and more than 45 days of cover.
    """
    landed = compute_landed_cost(
        dfs["po_line_items"], dfs["purchase_orders"], as_of_date
    )
    stock = compute_current_stock(dfs["inventory_movements"], as_of_date)
    velocity_30 = compute_sales_velocity(
        dfs["line_items"], dfs["orders"], as_of_date, window_days=30
    )
    base = _attach_days_of_stock(stock, velocity_30, window_days=30)
    base = base.merge(landed, on="variant_id", how="inner")
    base["total_cash_tied_gbp"] = (
        base["current_stock_units"].clip(lower=0) * base["avg_landed_cost_gbp"]
    )

    slow = base[
        (base["current_stock_units"] > 0)
        & (base["avg_daily_sales"] < SLOW_STOCK_MAX_DAILY)
        & (base["avg_daily_sales"] > 0)
        & (base["days_of_stock"] > SLOW_STOCK_MIN_DAYS)
    ].copy()

    meta = dfs["variants"].merge(
        dfs["products"][["product_id", "title", "gender_segment"]],
        on="product_id",
        how="left",
    )[["variant_id", "sku", "title", "gender_segment"]]
    slow = slow.merge(meta, on="variant_id", how="left")
    slow = slow.rename(columns={"title": "product_title"})
    slow["recommended_action"] = "Markdown or bundle — slow sell-through (<1 unit/day)"
    return slow[
        [
            "variant_id",
            "sku",
            "product_title",
            "gender_segment",
            "current_stock_units",
            "avg_landed_cost_gbp",
            "total_cash_tied_gbp",
            "days_of_stock",
            "avg_daily_sales",
            "recommended_action",
        ]
    ].sort_values("total_cash_tied_gbp", ascending=False)


def find_reorder_candidates(
    dfs: dict[str, pd.DataFrame],
    as_of_date: date = DATASET_TODAY,
) -> pd.DataFrame:
    """
    Variants with under 14 days of stock and positive 30d velocity.
    """
    landed = compute_landed_cost(
        dfs["po_line_items"], dfs["purchase_orders"], as_of_date
    )
    stock = compute_current_stock(dfs["inventory_movements"], as_of_date)
    velocity_30 = compute_sales_velocity(
        dfs["line_items"], dfs["orders"], as_of_date, window_days=30
    )
    velocity_60 = compute_sales_velocity(
        dfs["line_items"], dfs["orders"], as_of_date, window_days=60
    )[["variant_id", "units_sold"]].rename(columns={"units_sold": "units_sold_60d"})

    base = _attach_days_of_stock(stock, velocity_30, window_days=30)
    base = base.merge(velocity_60, on="variant_id", how="left")
    base["units_sold_60d"] = base["units_sold_60d"].fillna(0)
    base = base.merge(landed, on="variant_id", how="inner")
    base["units_sold_30d"] = base["units_sold"]

    trend_up = base["units_sold_30d"] > (base["units_sold_60d"] - base["units_sold_30d"]).clip(
        lower=0
    )
    low_cover = (base["days_of_stock"] > 0) & (
        base["days_of_stock"] < REORDER_MAX_DAYS_STOCK
    )
    reorder = base[
        (base["current_stock_units"] > 0)
        & (base["avg_daily_sales"] > 0)
        & low_cover
        & trend_up
    ].copy()

    if reorder.empty:
        return pd.DataFrame(
            columns=[
                "variant_id",
                "sku",
                "product_title",
                "supplier_name",
                "suggested_qty",
                "unit_cost_gbp",
                "po_value_gbp",
                "days_of_stock",
                "units_sold_30d",
            ]
        )

    meta = dfs["variants"].merge(
        dfs["products"][["product_id", "title"]],
        on="product_id",
        how="left",
    )[["variant_id", "sku", "title"]]
    reorder = reorder.merge(meta, on="variant_id", how="left")
    reorder = reorder.rename(columns={"title": "product_title", "avg_landed_cost_gbp": "unit_cost_gbp"})
    reorder["suggested_qty"] = (
        (REORDER_MAX_DAYS_STOCK * 2 * reorder["avg_daily_sales"]).round().astype(int).clip(lower=10)
    )
    reorder["po_value_gbp"] = reorder["suggested_qty"] * reorder["unit_cost_gbp"]

    suppliers = dfs.get("suppliers")
    if suppliers is not None and not suppliers.empty:
        po_recent = dfs["purchase_orders"].sort_values("created_at", ascending=False)
        if "supplier_id" in po_recent.columns:
            default_supplier = suppliers.iloc[0]["name"] if "name" in suppliers.columns else "Primary supplier"
            reorder["supplier_name"] = default_supplier
        else:
            reorder["supplier_name"] = "Primary supplier"
    else:
        reorder["supplier_name"] = "Primary supplier"

    return reorder[
        [
            "variant_id",
            "sku",
            "product_title",
            "supplier_name",
            "suggested_qty",
            "unit_cost_gbp",
            "po_value_gbp",
            "days_of_stock",
            "units_sold_30d",
        ]
    ].sort_values("po_value_gbp", ascending=False)


def find_ad_waste(
    google_ads: pd.DataFrame,
    meta_ads: pd.DataFrame,
    orders: pd.DataFrame,
    as_of_date: date = DATASET_TODAY,
    window_days: int = 14,
) -> pd.DataFrame:
    """
    Campaigns with negative ROI: 14d spend exceeds UTM-attributed order revenue.
    """
    as_of = _as_timestamp(as_of_date)
    cutoff = as_of - timedelta(days=window_days)

    g = google_ads.copy()
    g["date"] = pd.to_datetime(g["date"], errors="coerce")
    g = g[(g["date"] >= cutoff) & (g["date"] <= as_of)]
    g["platform"] = "google"

    m = meta_ads.copy()
    m["date"] = pd.to_datetime(m["date"], errors="coerce")
    m = m[(m["date"] >= cutoff) & (m["date"] <= as_of)]
    m["platform"] = "meta"

    ad_cols = ["date", "campaign_name", "spend_gbp", "conversions", "platform"]
    ads = pd.concat([g[ad_cols], m[ad_cols]], ignore_index=True)
    spend = (
        ads.groupby(["campaign_name", "platform"], as_index=False)
        .agg(spend_gbp=("spend_gbp", "sum"), conversions=("conversions", "sum"))
    )

    ord_df = orders.copy()
    ord_df["created_at"] = pd.to_datetime(ord_df["created_at"], errors="coerce")
    recent = ord_df[(ord_df["created_at"] >= cutoff) & (ord_df["created_at"] <= as_of)]
    recent = recent[recent["utm_campaign"].notna() & (recent["utm_campaign"] != "")]
    revenue = (
        recent.groupby("utm_campaign", as_index=False)["total_price"]
        .sum()
        .rename(columns={"utm_campaign": "campaign_name", "total_price": "attributed_revenue"})
    )

    merged = spend.merge(revenue, on="campaign_name", how="left")
    merged["attributed_revenue"] = merged["attributed_revenue"].fillna(0)
    merged["roi"] = np.where(
        merged["spend_gbp"] > 0,
        (merged["attributed_revenue"] - merged["spend_gbp"]) / merged["spend_gbp"],
        0.0,
    )
    waste = merged[
        (merged["spend_gbp"] > 0)
        & (
            (merged["attributed_revenue"] < merged["spend_gbp"])
            | (merged["conversions"] <= 0)
        )
    ].copy()

    waste["days_no_conversion"] = window_days
    waste["recommended_action"] = np.where(
        waste["attributed_revenue"] < waste["spend_gbp"],
        "Pause campaign — negative 14d ROI (spend > attributed revenue)",
        "Pause campaign — zero platform conversions in 14d",
    )
    return waste.sort_values("spend_gbp", ascending=False)[
        [
            "campaign_name",
            "platform",
            "spend_gbp",
            "conversions",
            "attributed_revenue",
            "roi",
            "days_no_conversion",
            "recommended_action",
        ]
    ]


def compute_cash_liberation_total(
    dead_inv: pd.DataFrame,
    late_pos: pd.DataFrame,
    ad_waste: pd.DataFrame,
) -> dict[str, float | int]:
    """Aggregate recoverable cash across leak categories."""
    inventory_gbp = float(dead_inv["total_cash_tied_gbp"].sum()) if not dead_inv.empty else 0.0
    supplier_gbp = float(late_pos["recoverable_gbp"].sum()) if not late_pos.empty else 0.0
    ads_gbp = float(ad_waste["spend_gbp"].sum()) if not ad_waste.empty else 0.0
    total = inventory_gbp + supplier_gbp + ads_gbp
    item_count = len(dead_inv) + len(late_pos) + len(ad_waste)
    return {
        "total_gbp": total,
        "inventory_gbp": inventory_gbp,
        "supplier_gbp": supplier_gbp,
        "ads_gbp": ads_gbp,
        "item_count": item_count,
    }


def compute_cash_position(
    dfs: dict[str, pd.DataFrame],
    as_of_date: date = DATASET_TODAY,
) -> dict[str, float]:
    """
    Bank balance from latest transaction on or before as_of_date.

    Payables from overdue POs; receivables from recent paid orders (3-day settlement proxy).
    """
    as_of = _as_timestamp(as_of_date)
    bank = dfs["bank_transactions"].copy()
    bank["date"] = pd.to_datetime(bank["date"], errors="coerce")
    hist = bank[bank["date"] <= as_of].sort_values("date")
    bank_balance = float(hist.iloc[-1]["balance_gbp"]) if not hist.empty else 0.0

    suppliers = dfs.get("suppliers")
    late = find_late_pos(dfs["purchase_orders"], as_of_date, suppliers)
    outstanding = float(late["recoverable_gbp"].sum()) if not late.empty else 0.0

    orders = dfs["orders"].copy()
    orders["created_at"] = pd.to_datetime(orders["created_at"], errors="coerce")
    settlement_start = as_of - timedelta(days=3)
    recent_paid = orders[
        (orders["created_at"] > settlement_start)
        & (orders["created_at"] <= as_of)
        & (orders["financial_status"] == "paid")
    ]
    expected_receivables = float(recent_paid["total_price"].sum())

    net_cash = bank_balance - outstanding + expected_receivables
    return {
        "bank_balance_gbp": bank_balance,
        "outstanding_payables_gbp": outstanding,
        "expected_receivables_gbp": expected_receivables,
        "net_cash_gbp": net_cash,
    }


def run_backtest(
    dfs: dict[str, pd.DataFrame],
    as_of_date: date,
    horizon_days: int = 30,
) -> dict[str, Any]:
    """
    Run leak detection on a historical snapshot and measure forward outcomes.

    Returns raw DataFrames plus summary metrics for the API layer.
    """
    snapshot = filter_dfs_to_date(dfs, as_of_date)
    suppliers = snapshot.get("suppliers")
    if suppliers is None:
        suppliers = dfs.get("suppliers")
    dead = find_dead_inventory(snapshot, as_of_date)
    late = find_late_pos(snapshot["purchase_orders"], as_of_date, suppliers)
    ad = find_ad_waste(
        snapshot["google_ads_daily"],
        snapshot["meta_ads_daily"],
        snapshot["orders"],
        as_of_date,
    )

    as_of_ts = _as_timestamp(as_of_date)
    end_ts = _as_timestamp(as_of_date + timedelta(days=horizon_days))

    recovered_gbp = 0.0
    if dead.empty:
        summary = f"No dead-stock flags on {as_of_date.isoformat()}."
    else:
        orders = dfs["orders"].copy()
        orders["created_at"] = pd.to_datetime(orders["created_at"], errors="coerce")
        future = (
            dfs["line_items"]
            .merge(orders[["order_id", "created_at"]], on="order_id", how="inner")
            .query("created_at > @as_of_ts and created_at <= @end_ts")
        )
        flagged_ids = set(dead["variant_id"])
        future_flagged = future[future["variant_id"].isin(flagged_ids)]
        units_by_variant = future_flagged.groupby("variant_id")["quantity"].sum()

        for _, row in dead.iterrows():
            vid = row["variant_id"]
            sold = float(units_by_variant.get(vid, 0))
            unit_value = float(row["avg_landed_cost_gbp"])
            recovered_gbp += min(float(row["total_cash_tied_gbp"]), sold * unit_value)

        total_units = int(future_flagged["quantity"].sum()) if not future_flagged.empty else 0
        summary = (
            f"In the {horizon_days} days after {as_of_date.isoformat()}, "
            f"{len(dead)} flagged SKUs sold {total_units} units; "
            f"estimated £{recovered_gbp:,.0f} cash freed at landed cost."
        )

    po_recovered = 0.0
    po_note = ""
    if not late.empty:
        po = dfs["purchase_orders"].copy()
        po["actual_delivery"] = pd.to_datetime(po["actual_delivery"], errors="coerce")
        for _, row in late.iterrows():
            po_id = row["po_id"]
            match = po[po["po_id"] == po_id]
            if match.empty:
                continue
            delivery = match.iloc[0]["actual_delivery"]
            if pd.notna(delivery) and as_of_ts < delivery <= end_ts:
                po_recovered += float(row["recoverable_gbp"])
        po_note = (
            f" {len(late)} overdue PO(s) flagged; "
            f"£{po_recovered:,.0f} deposit/balance recovered if chased."
        )

    ad_saved = 0.0
    ad_note = ""
    if not ad.empty:
        g = dfs["google_ads_daily"].copy()
        g["date"] = pd.to_datetime(g["date"], errors="coerce")
        m = dfs["meta_ads_daily"].copy()
        m["date"] = pd.to_datetime(m["date"], errors="coerce")
        for _, row in ad.iterrows():
            platform = row["platform"]
            name = row["campaign_name"]
            src = g if platform == "google" else m
            future_spend = src[
                (src["campaign_name"] == name)
                & (src["date"] > as_of_ts)
                & (src["date"] <= end_ts)
            ]["spend_gbp"].sum()
            ad_saved += float(future_spend)
        ad_note = (
            f" {len(ad)} negative-ROI campaigns; "
            f"£{ad_saved:,.0f} ad spend could have been avoided."
        )

    total_recovered = recovered_gbp + po_recovered + ad_saved
    summary = summary + po_note + ad_note

    return {
        "dead_inv": dead,
        "late_pos": late,
        "ad_waste": ad,
        "actual_outcome_summary": summary,
        "estimated_cash_recovered_gbp": total_recovered,
        "inventory_recovered_gbp": recovered_gbp,
        "po_recovered_gbp": po_recovered,
        "ad_saved_gbp": ad_saved,
    }


def find_best_backtest_date(
    dfs: dict[str, pd.DataFrame],
    as_of_end: date = DATASET_TODAY,
    lookback_months: int = 6,
    horizon_days: int = 30,
) -> dict[str, Any]:
    """
    Scan monthly snapshots in the lookback window for the highest recovery story.
    """
    from datetime import timedelta

    best_date: date | None = None
    best_recovery = 0.0
    best_summary = ""
    candidates: list[dict[str, Any]] = []

    end = as_of_end - timedelta(days=horizon_days + 7)
    start = end - timedelta(days=lookback_months * 30)
    cursor = start.replace(day=1)
    while cursor <= end:
        try:
            result = run_backtest(dfs, cursor, horizon_days=horizon_days)
            recovery = float(result["estimated_cash_recovered_gbp"])
            candidates.append(
                {
                    "date": cursor.isoformat(),
                    "estimated_cash_recovered_gbp": recovery,
                    "summary": result["actual_outcome_summary"],
                }
            )
            if recovery > best_recovery:
                best_recovery = recovery
                best_date = cursor
                best_summary = result["actual_outcome_summary"]
        except Exception:
            pass
        if cursor.month == 12:
            cursor = date(cursor.year + 1, 1, 1)
        else:
            cursor = date(cursor.year, cursor.month + 1, 1)

    if best_date is None and candidates:
        best = max(candidates, key=lambda c: c["estimated_cash_recovered_gbp"])
        best_date = date.fromisoformat(best["date"])
        best_recovery = best["estimated_cash_recovered_gbp"]
        best_summary = best["summary"]

    return {
        "best_date": best_date.isoformat() if best_date else as_of_end.isoformat(),
        "estimated_cash_recovered_gbp": best_recovery,
        "summary": best_summary or "No strong backtest signal in lookback window.",
        "candidates": candidates[:12],
    }


def filter_dfs_to_date(dfs: dict[str, pd.DataFrame], as_of_date: date) -> dict[str, pd.DataFrame]:
    """Return a shallow copy of dfs with rows on or before as_of_date (for backtests)."""
    as_of = _as_timestamp(as_of_date)
    out: dict[str, pd.DataFrame] = {}
    date_columns: dict[str, list[str]] = {
        "orders": ["created_at"],
        "inventory_movements": ["date"],
        "purchase_orders": ["created_at", "expected_delivery", "actual_delivery"],
        "bank_transactions": ["date"],
        "google_ads_daily": ["date"],
        "meta_ads_daily": ["date"],
        "line_items": [],
        "po_line_items": [],
        "variants": [],
        "products": ["created_at"],
        "email_events": [],
    }
    for key, df in dfs.items():
        filtered = df.copy()
        for col in date_columns.get(key, []):
            if col in filtered.columns:
                filtered[col] = pd.to_datetime(filtered[col], errors="coerce")
                filtered = filtered[filtered[col].isna() | (filtered[col] <= as_of)]
        out[key] = filtered
    return out


if __name__ == "__main__":
    import sys

    from config import DEFAULT_DATA_DIR
    from data_loader import DataLoader

    data_path = sys.argv[1] if len(sys.argv) > 1 else str(DEFAULT_DATA_DIR)
    loader = DataLoader(data_path)
    result = loader.load()
    dfs = result["dfs"]

    print("=== Validation ===")
    print("PASSED" if result["validation"]["passed"] else "FAILED")
    if result["validation"]["output"]:
        print(result["validation"]["output"][:500])

    print("\n=== Dead Inventory (top 10) ===")
    dead = find_dead_inventory(dfs, DATASET_TODAY)
    if dead.empty:
        print("(none)")
    else:
        print(
            dead[["product_title", "current_stock_units", "total_cash_tied_gbp"]].head(10)
        )

    print("\n=== Late POs ===")
    suppliers = dfs.get("suppliers")
    late = find_late_pos(dfs["purchase_orders"], DATASET_TODAY, suppliers)
    print(late if not late.empty else "(none)")

    print("\n=== Ad waste (top 5) ===")
    ad = find_ad_waste(
        dfs["google_ads_daily"],
        dfs["meta_ads_daily"],
        dfs["orders"],
        DATASET_TODAY,
    )
    print(ad.head(5) if not ad.empty else "(none)")

    print("\n=== Total Cash Liberation ===")
    total = compute_cash_liberation_total(dead, late, ad)
    print(f"£{total['total_gbp']:,.0f} recoverable ({total['item_count']} items)")
    print(
        f"  inventory £{total['inventory_gbp']:,.0f} | "
        f"supplier £{total['supplier_gbp']:,.0f} | "
        f"ads £{total['ads_gbp']:,.0f}"
    )
