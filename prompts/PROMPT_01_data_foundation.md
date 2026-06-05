# PROMPT_01 — Data Foundation
**Paste this into Cursor Chat to start Day 1**

---

Read the docs in `docs/TRD.md`, `docs/SE.md`, and `.cursor/rules/01-data-layer.mdc` before writing any code.

Build the complete data layer for CashFly. Create these files exactly:

## `backend/data_loader.py`

Create a `DataLoader` class that:
1. Accepts a `data_dir: str` path
2. Loads these CSV files into pandas DataFrames (with proper date parsing):
   - `orders.csv` → parse `created_at`
   - `line_items.csv`
   - `variants.csv`
   - `products.csv`
   - `inventory_movements.csv` → parse `date` or `created_at`
   - `po_line_items.csv`
   - `purchase_orders.csv` → parse `delivery_date`, `created_at`
   - `bank_transactions.csv` → parse `date`
   - `google_ads_daily.csv` → parse `date`
   - `meta_ads_daily.csv` → parse `date`
   - `email_campaigns.csv`
   - `email_events.csv`
3. Runs `validate.py` via `subprocess.run` and captures output
4. Returns `{"dfs": dict[str, DataFrame], "validation": {"passed": bool, "output": str}}`
5. Raises `FileNotFoundError` with the missing filename if any CSV is absent

## `backend/cash_engine.py`

Implement these functions with full type hints and docstrings.
Use `DATASET_TODAY = date(2026, 6, 1)` as the default `as_of_date`.

```python
def compute_landed_cost(po_line_items, purchase_orders, as_of_date) -> pd.DataFrame
# Returns: DataFrame with [variant_id, avg_landed_cost_gbp]

def compute_current_stock(inventory_movements, as_of_date) -> pd.DataFrame  
# Returns: DataFrame with [variant_id, current_stock_units]

def compute_sales_velocity(line_items, orders, as_of_date, window_days=30) -> pd.DataFrame
# Returns: DataFrame with [variant_id, units_sold, avg_daily_sales, days_of_stock]

def find_dead_inventory(dfs, as_of_date) -> pd.DataFrame
# Joins landed cost + stock + velocity + variants + products
# Returns top dead stock items sorted by cash_at_risk_gbp desc
# Columns: [variant_id, sku, product_title, gender_segment, current_stock_units, 
#            avg_landed_cost_gbp, total_cash_tied_gbp, days_of_stock, 
#            units_sold_last_7d, recommended_action]

def find_late_pos(purchase_orders, as_of_date) -> pd.DataFrame
# Returns POs where expected_delivery < as_of_date and status != 'delivered'
# Columns: [po_id, supplier_name, deposit_paid_gbp, balance_gbp, days_overdue, 
#            recoverable_gbp, recommended_action]

def find_ad_waste(google_ads, meta_ads, orders, as_of_date, window_days=7) -> pd.DataFrame
# Join ad spend to orders via utm_campaign
# Return campaigns with spend > 0 and attributed_revenue = 0 in last window_days
# Columns: [campaign_name, platform, spend_gbp, conversions, days_no_conversion,
#            recommended_action]

def compute_cash_liberation_total(dead_inv, late_pos, ad_waste) -> dict
# Returns: {total_gbp, inventory_gbp, supplier_gbp, ads_gbp, item_count}
```

## `backend/models.py`

Create all Pydantic models as specified in `docs/SE.md` section 3.1.
Include `CashLeak`, `CashPosition`, `CashLeaksResponse`, `BacktestResult`, 
`LoadDataResponse`, `HealthResponse`, `EmailDraftResponse`.

## Tests (inline, not a test file)

At the bottom of `cash_engine.py`, add:
```python
if __name__ == "__main__":
    import sys
    from data_loader import DataLoader
    
    loader = DataLoader(sys.argv[1] if len(sys.argv) > 1 else "../data")
    result = loader.load()
    dfs = result["dfs"]
    
    print("=== Dead Inventory ===")
    dead = find_dead_inventory(dfs, DATASET_TODAY)
    print(dead[["product_title", "current_stock_units", "total_cash_tied_gbp"]].head(10))
    
    print("\n=== Late POs ===")
    late = find_late_pos(dfs["purchase_orders"], DATASET_TODAY)
    print(late)
    
    print("\n=== Total Cash Liberation ===")
    ad = find_ad_waste(dfs["google_ads_daily"], dfs["meta_ads_daily"], dfs["orders"], DATASET_TODAY)
    total = compute_cash_liberation_total(dead, late, ad)
    print(f"£{total['total_gbp']:,.0f} recoverable")
```

**When done:** Run `python cash_engine.py ../data` and paste the output here so we can verify the numbers before building the API.
