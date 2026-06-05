# PROMPT_04 — Cash Leaks Polish & Reconciliation Proof
**Day 2 — after frontend shell is rendering live data**

---

The basic UI is running. Now make the cash leaks airtight and demo-ready.

## 1. Reconciliation Proof Panel

In the Dashboard page, add a collapsible "Show reconciliation" section that displays:
```
Bank balance (from bank_transactions):     £XX,XXX
+ Expected Shopify payouts:                £XX,XXX  
- Outstanding supplier payments:          -£XX,XXX
= Net cash position:                       £XX,XXX

Total COGS sold (landed cost × units):     £XX,XXX
Total supplier payments (bank outflows):   £XX,XXX
Variance:                                  £XXX  ← should be < 5%
```
This is your live proof during the demo that the numbers are real.

## 2. Upgrade `find_dead_inventory` in `cash_engine.py`

Add these two computed columns:
```python
df["days_since_last_sale"] = (as_of_date - df["last_sale_date"]).dt.days
df["weekly_sales_last_4w"] = df["units_sold_last_28d"] / 4
```
And add gender_segment to the output — flag womenswear items separately:
```python
df["is_womenswear"] = df["gender_segment"].str.lower().isin(["women", "female", "womenswear"])
```
Add a note to womenswear items: "New line (Dec 2025) — higher return risk, recommend smaller reorder"

## 3. Upgrade `LeakCard.tsx`

Add a "cash recovery estimate" field:
- For inventory: show expected recovery at 70% sell-through × selling price
- For POs: show deposit amount as recoverable
- Format: "Est. recovery: £X,XXX"

Add a confidence badge:
- High (green): days_of_stock > 90 or days_overdue > 30
- Medium (amber): days_of_stock 45-90
- Low (grey): borderline cases

## 4. Add `/leaks` Tab Filtering

Make tabs actually filter:
```typescript
const filtered = leaks.filter(l => 
  activeTab === "all" ? true : l.category === tabCategoryMap[activeTab]
)
```
Show count badge on each tab: "Inventory (7)" "Suppliers (3)" "Ad Spend (4)"

## 5. "Total Cash Liberation" Summary Bar

Sticky bar at top of `/leaks` page:
```
[📦 Inventory: £12,400]  [🏭 Suppliers: £3,200]  [📢 Ads: £2,600]  ||  TOTAL: £18,200
```
Each section clickable to jump to that tab.

## 6. Export CSV Button

On the `/leaks` page, "Export All Leaks" button:
```typescript
const csv = leaks.map(l => `${l.title},${l.category},${l.cash_at_risk_gbp},${l.recommended_action}`)
const blob = new Blob([["Name,Category,Cash At Risk,Action\n", ...csv].join("\n")])
// trigger download
```

## 7. Demo Scenarios — Verify These Work

Run manually and confirm these outputs exist in the UI:

**Scenario A:** Dead inventory — find a hoodie or sweatpant SKU with:
- current_stock > 100 units
- days_of_stock > 45
- cash_tied > £3,000
→ Should appear in top 5 leaks

**Scenario B:** Late PO — find a PO where:
- delivery_date < 2026-06-01
- status != 'delivered'
- deposit_paid > £0
→ Should appear in supplier section

**Scenario C:** Ad waste — find a Google or Meta campaign where:
- spend > £0 in last 7 days
- attributed orders = 0 (no utm_campaign match in orders table)
→ Should appear in ad spend section

If any scenario returns empty, debug and fix in `cash_engine.py`.

**When done:** Run through all three scenarios manually and confirm each LeakCard shows:
- Correct £ amount (verify manually against raw CSV)
- Correct recommended action
- Non-zero recoverable estimate
