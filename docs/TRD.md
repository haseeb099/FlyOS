# Technical Requirements Document
# CashFly — Cash-to-Cash Cycle Optimizer for Pretty Fly
**Hackathon: Wayflyer × Fin | June 3–5, 2026 | London**

---

## 1. System Overview

CashFly is a single-page, data-driven web application that ingests Pretty Fly's 21-file CSV/JSON dataset and surfaces actionable cash liberation recommendations. It uses pandas/SQL for all numerical computation and Claude (Anthropic API) only for natural language explanation and email copy generation.

---

## 2. Tech Stack

| Layer | Choice | Reason |
|-------|--------|--------|
| Frontend | Next.js 14 (App Router) | Fast SSR, easy API routes |
| Data layer | Python (pandas) via Next.js API routes calling a FastAPI microservice | Pandas is fastest for joins on CSV data |
| Backend API | FastAPI (Python 3.11) | Lightweight, auto-docs, easy to run alongside Next |
| LLM | Anthropic Claude claude-sonnet-4-20250514 via SDK | Natural language explanations only |
| Styling | Tailwind CSS + shadcn/ui | Rapid premium UI |
| Charts | Recharts | Zero-config, React-native |
| State | Zustand | Lightweight client state |
| Data loading | File upload (drag-drop CSV folder) OR local path mount | Hackathon context |
| Validation | Python validate.py (provided) | Run on startup |

---

## 3. Data Architecture

### 3.1 Core Tables Used (4 primary, 4 supporting)

**Primary (cash computation):**
- `bank_transactions.csv` — ground truth cash in/out
- `inventory_movements.csv` — stock in/out per variant
- `po_line_items.csv` — landed cost per variant
- `line_items.csv` — units sold per variant

**Supporting (enrichment):**
- `purchase_orders.csv` — PO status, delivery dates
- `variants.csv` — SKU, product_id
- `products.csv` — title, product_type, gender_segment
- `orders.csv` — created_at, customer_id

**Optional (if time permits):**
- `google_ads_daily.csv` + `meta_ads_daily.csv` — ad waste detection
- `email_campaigns.csv` + `email_events.csv` — email draft context

### 3.2 Key Computed Metrics

```
landed_cost_per_variant = AVG(po_line_items.unit_cost) WHERE delivery_date <= today
current_stock_per_variant = SUM(inventory_movements.quantity_change) GROUP BY variant_id
cash_tied_in_inventory = current_stock * landed_cost_per_variant
days_of_stock = current_stock / avg_daily_sales_last_30d
cash_at_risk = cash_tied_in_inventory WHERE days_of_stock > 45 AND units_sold_last_7d < 2
unpaid_po_balance = SUM(po.total_amount - po.deposit_paid) WHERE status != 'delivered'
```

### 3.3 Reconciliation Constraint
All cash figures MUST reconcile against `bank_transactions`. The FastAPI service runs `validate.py` on data load. If validation fails, the UI shows an error before proceeding.

---

## 4. API Endpoints (FastAPI)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/load-data` | Accept data folder path, run validate.py, load all CSVs |
| GET | `/api/cash-position` | Returns current cash position from bank_transactions |
| GET | `/api/cash-leaks` | Returns top 10 cash leak items (inventory + POs + ads) |
| GET | `/api/backtest?date=YYYY-MM-DD` | Runs the algorithm on a historical date |
| POST | `/api/generate-email` | Claude generates email copy for a dead stock item |
| GET | `/api/health` | Validator status |

---

## 5. Frontend Pages

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | `Dashboard` | Cash position summary + top 3 leaks |
| `/leaks` | `LeaksTable` | Full ranked list of cash leaks with actions |
| `/backtest` | `Backtest` | Date picker → historical recommendations |
| `/email` | `EmailDraft` | LLM-generated email campaigns |

---

## 6. Cash Leak Categories

### Category 1: Dead Inventory
- Criteria: `days_of_stock > 45` AND `units_sold_last_7d < 2`
- Output: `{variant, product_title, units, cash_tied, recommended_action}`
- Action: "Bundle & Save" email or markdown discount

### Category 2: Late Supplier POs
- Criteria: PO `expected_delivery < today` AND `status != delivered`
- Output: `{po_id, supplier_name, prepaid_amount, days_overdue}`
- Action: "Chase or cancel" with recoverable deposit amount

### Category 3: Ad Spend Waste
- Criteria: Campaign with `spend_last_7d > 0` AND `attributed_revenue_last_7d = 0`
- Output: `{campaign_name, platform, spend_wasted, days_no_conversion}`
- Action: "Pause campaign"

---

## 7. Backtesting Logic

1. User selects a historical date D (e.g., 2026-02-01)
2. System filters all data to `date <= D`
3. Runs the same cash leak algorithm on this snapshot
4. Shows what would have been recommended
5. Then shows what actually happened in the 30 days after D (using real data)
6. Computes: "If recommendation was followed, estimated cash recovered = £X"

---

## 8. LLM Integration (Claude)

**Only used for:**
- Natural language explanation of why a leak matters
- Email subject line + body copy for dead stock campaigns
- One-sentence "CFO insight" for each leak

**Never used for:**
- Number computation
- Data joins
- Business logic decisions

**Prompt pattern:**
```
System: You are a DTC finance analyst for Pretty Fly, a London streetwear brand.
User: We have 340 units of [product] sitting for [X] days. Landed cost: £[Y]/unit.
      Write a 3-sentence explanation of the cash risk and a promotional email subject line.
```

---

## 9. Performance Requirements

- Data load: < 5 seconds for all 21 files
- Cash leak computation: < 3 seconds
- LLM call: < 10 seconds (streaming preferred)
- No external database — all in-memory pandas DataFrames

---

## 10. Error Handling

- Validate.py failure → Block UI, show reconciliation errors
- Missing CSV → Show which file is missing, list required files
- LLM timeout → Show computed data without explanation, retry button
- Division by zero in days-of-stock → Default to 999 (infinite)

---

## 11. Demo Scenarios (Must Work Flawlessly)

1. **Dead stock recovery**: Black Hoodie XL → £X tied up → email draft
2. **Late PO recovery**: Supplier X → £Y prepaid → overdue by Z days
3. **Ad waste detection**: Campaign "Summer Flash" → £Z spent, 0 conversions
4. **Backtest**: Feb 1 2026 → what we'd have recommended → what happened
5. **Total cash liberation**: "£18,000 recoverable by end of June"
