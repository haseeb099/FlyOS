"""Export Klaviyo-style customer segments for inventory leak actions."""

from __future__ import annotations

from datetime import date, timedelta
from io import StringIO

import pandas as pd

from config import DATASET_TODAY


def _parse_variant_id(leak_id: str) -> str | None:
    if leak_id.startswith("inv_"):
        return leak_id[4:]
    if leak_id.startswith("slow_"):
        return leak_id[5:]
    return None


def export_dead_stock_segment(
    dfs: dict[str, pd.DataFrame],
    leak_id: str,
    as_of_date: date = DATASET_TODAY,
    *,
    lookback_days: int = 90,
) -> tuple[str, int]:
    """
    Customers who bought the same product family in last 90d but not the stuck variant.

    Returns CSV text and row count.
    """
    variant_id = _parse_variant_id(leak_id)
    if variant_id is None:
        raise ValueError(f"Segment export only supports inventory leaks, got: {leak_id}")

    customers = dfs.get("customers")
    if customers is None or customers.empty:
        raise ValueError("customers.csv not loaded — required for segment export")

    variants = dfs["variants"]
    products = dfs["products"]
    variant_row = variants[variants["variant_id"] == variant_id]
    if variant_row.empty:
        raise ValueError(f"Unknown variant: {variant_id}")

    product_id = variant_row.iloc[0]["product_id"]
    product_row = products[products["product_id"] == product_id]
    if product_row.empty:
        raise ValueError(f"Unknown product for variant: {variant_id}")

    family_key = product_row.iloc[0].get("product_type") or product_row.iloc[0].get("title", "")
    family_variants = variants.merge(
        products[["product_id", "product_type", "title"]],
        on="product_id",
        how="left",
    )
    if "product_type" in family_variants.columns:
        same_family = family_variants[
            family_variants["product_type"] == product_row.iloc[0].get("product_type")
        ]["variant_id"].tolist()
    else:
        title_prefix = str(product_row.iloc[0]["title"]).split()[0]
        same_family = family_variants[
            family_variants["title"].astype(str).str.startswith(title_prefix)
        ]["variant_id"].tolist()

    as_of = pd.Timestamp(as_of_date)
    cutoff = as_of - timedelta(days=lookback_days)

    orders = dfs["orders"].copy()
    orders["created_at"] = pd.to_datetime(orders["created_at"], errors="coerce")
    recent_orders = orders[
        (orders["created_at"] >= cutoff) & (orders["created_at"] <= as_of)
    ]

    line_items = dfs["line_items"]
    family_purchases = line_items[
        line_items["variant_id"].isin(same_family)
    ].merge(recent_orders[["order_id", "customer_id", "created_at"]], on="order_id")

    stuck_purchases = line_items[line_items["variant_id"] == variant_id].merge(
        orders[["order_id", "customer_id"]], on="order_id"
    )
    stuck_customers = set(stuck_purchases["customer_id"].dropna().unique())

    segment_orders = family_purchases[
        ~family_purchases["customer_id"].isin(stuck_customers)
    ]
    if segment_orders.empty:
        out = pd.DataFrame(
            columns=[
                "email",
                "first_name",
                "last_name",
                "last_order_date",
                "segment_tag",
            ]
        )
    else:
        last_by_customer = (
            segment_orders.groupby("customer_id", as_index=False)["created_at"]
            .max()
            .rename(columns={"created_at": "last_order_date"})
        )
        cust_cols = ["customer_id", "email"]
        for col in ("first_name", "last_name"):
            if col in customers.columns:
                cust_cols.append(col)

        merged = last_by_customer.merge(
            customers[cust_cols],
            on="customer_id",
            how="inner",
        )
        sku = variant_row.iloc[0].get("sku", variant_id)
        merged["segment_tag"] = f"dead_stock_crosssell_{sku}"
        merged["last_order_date"] = merged["last_order_date"].dt.strftime("%Y-%m-%d")
        out = merged[
            ["email", "first_name", "last_name", "last_order_date", "segment_tag"]
        ].drop_duplicates(subset=["email"])

    buffer = StringIO()
    out.to_csv(buffer, index=False)
    return buffer.getvalue(), len(out)
