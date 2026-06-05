# Software Engineering Specification
# CashFly — Implementation Blueprint
**For Cursor AI-assisted development**

---

## 1. Repository Structure

```
cashfly/
├── .cursor/
│   └── rules/
│       ├── 00-project.mdc
│       ├── 01-data-layer.mdc
│       ├── 02-api.mdc
│       ├── 03-frontend.mdc
│       └── 04-llm.mdc
├── docs/
│   ├── PRD.md
│   ├── TRD.md
│   └── SE.md
├── prompts/
│   ├── PROMPT_01_data_foundation.md
│   ├── PROMPT_02_api_server.md
│   ├── PROMPT_03_frontend_shell.md
│   ├── PROMPT_04_cash_leaks.md
│   ├── PROMPT_05_backtest.md
│   └── PROMPT_06_llm_email.md
├── backend/
│   ├── main.py              # FastAPI app entry
│   ├── data_loader.py       # CSV loading + validate.py runner
│   ├── cash_engine.py       # All pandas computation (NO LLM)
│   ├── llm_service.py       # Claude API calls ONLY
│   ├── models.py            # Pydantic response models
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx         # Dashboard
│   │   ├── leaks/page.tsx
│   │   ├── backtest/page.tsx
│   │   └── email/page.tsx
│   ├── components/
│   │   ├── CashMeter.tsx
│   │   ├── LeakCard.tsx
│   │   ├── ReconciliationBadge.tsx
│   │   ├── BacktestTimeline.tsx
│   │   └── EmailPreview.tsx
│   ├── lib/
│   │   ├── api.ts           # Fetch wrappers for FastAPI
│   │   └── types.ts         # TypeScript types
│   ├── package.json
│   └── tailwind.config.ts
├── data/                    # Pretty Fly CSVs go here (gitignored)
│   └── .gitkeep
└── README.md
```

---

## 2. Data Layer Specification (`cash_engine.py`)

### 2.1 Data Loading Contract
```python
# All functions receive pre-loaded DataFrames, never read files themselves
def compute_landed_cost(po_line_items: pd.DataFrame, purchase_orders: pd.DataFrame) -> pd.DataFrame:
    """Returns: variant_id, avg_landed_cost_gbp"""

def compute_current_stock(inventory_movements: pd.DataFrame) -> pd.DataFrame:
    """Returns: variant_id, current_stock_units"""

def compute_cash_in_inventory(stock: pd.DataFrame, cost: pd.DataFrame, variants: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    """Returns: variant_id, sku, product_title, current_stock, landed_cost, total_cash_tied"""

def compute_sales_velocity(line_items: pd.DataFrame, orders: pd.DataFrame, window_days: int = 30) -> pd.DataFrame:
    """Returns: variant_id, units_sold_last_N_days, days_of_stock_remaining"""

def find_dead_inventory(cash_df: pd.DataFrame, velocity_df: pd.DataFrame, 
                         min_days: int = 45, max_weekly_sales: int = 2) -> pd.DataFrame:
    """Returns: ranked dead stock items with cash_at_risk"""

def find_late_pos(purchase_orders: pd.DataFrame, as_of_date: date) -> pd.DataFrame:
    """Returns: late POs with recoverable_deposit_amount"""

def find_ad_waste(google_ads: pd.DataFrame, meta_ads: pd.DataFrame, 
                   orders: pd.DataFrame, window_days: int = 7) -> pd.DataFrame:
    """Returns: campaigns with spend_gbp and zero_conversions"""

def compute_total_cash_liberation(dead_inv: pd.DataFrame, late_pos: pd.DataFrame, ad_waste: pd.DataFrame) -> dict:
    """Returns: {total_gbp, breakdown_by_category}"""
```

### 2.2 Backtest Contract
```python
def backtest(all_dfs: dict, as_of_date: date) -> dict:
    """
    Filter all DataFrames to rows where date <= as_of_date.
    Run full cash leak algorithm.
    Return recommendations + actual_outcome (using full data).
    """
```

### 2.3 Data Validation
```python
def run_validator(data_dir: str) -> dict:
    """
    Runs validate.py via subprocess.
    Returns: {passed: bool, rules_total: int, rules_passed: int, failures: list[str]}
    """
```

---

## 3. API Specification (FastAPI)

### 3.1 Models (`models.py`)
```python
class CashLeak(BaseModel):
    id: str
    category: Literal["inventory", "supplier_po", "ad_spend"]
    title: str
    subtitle: str
    cash_at_risk_gbp: float
    units_or_days: str          # "340 units" or "18 days overdue"
    recommended_action: str
    recoverable_gbp: float
    confidence: Literal["high", "medium", "low"]

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

class BacktestResult(BaseModel):
    as_of_date: str
    recommendations: list[CashLeak]
    actual_outcome_summary: str
    estimated_cash_recovered_gbp: float
```

### 3.2 Routes (`main.py`)
```python
POST /api/load-data       body: {data_path: str}
GET  /api/cash-position   
GET  /api/cash-leaks      query: ?as_of_date=YYYY-MM-DD (default: today in dataset = 2026-06-01)
GET  /api/backtest        query: ?date=YYYY-MM-DD
POST /api/generate-email  body: {leak_id: str, variant_title: str, units: int, cash_tied: float}
GET  /api/health
```

---

## 4. Frontend Component Specification

### 4.1 `CashMeter.tsx`
- Animated counter from 0 to total_recoverable_gbp on mount
- Large bold number, amber color `#F59E0B`
- Subtitle: "recoverable by end of June"
- ReconciliationBadge inline

### 4.2 `LeakCard.tsx`
Props: `leak: CashLeak`
- Icon: 📦 inventory | 🏭 supplier | 📢 ads
- Category badge (color-coded)
- Title + subtitle
- Cash amount (large, amber)
- Recommended action (pill badge)
- CTA button: "Generate Email" | "Chase Supplier" | "Pause Campaign"

### 4.3 `BacktestTimeline.tsx`
- Date picker (limit to dataset range: Jun 2024 – May 2026)
- Two-column layout: "What we'd have said" | "What actually happened"
- Delta card: "Cash recovered if followed: £X"

### 4.4 `EmailPreview.tsx`
- Mock email client frame (dark)
- To, Subject, Body fields (LLM-generated, editable)
- "Copy to Clipboard" + "Download CSV" buttons
- Streaming: show text as it comes from Claude

---

## 5. LLM Integration (`llm_service.py`)

```python
SYSTEM_PROMPT = """
You are a DTC finance analyst for Pretty Fly, a London streetwear brand.
You write concise, plain-English explanations and email copy.
Never invent numbers. Only use the data provided to you.
Be direct. No filler phrases. Max 3 sentences per explanation.
"""

async def explain_cash_leak(leak: CashLeak) -> str:
    """Returns 2-3 sentence plain English explanation of why this leak matters."""

async def generate_email_campaign(variant_title: str, units: int, 
                                   cash_tied: float, open_rate: float) -> dict:
    """Returns {subject: str, body: str, discount_suggestion: str}"""
```

**Hard rules:**
- Never ask Claude to compute £ amounts — compute first, pass as context
- Always include `max_tokens=500` for explanations, `max_tokens=300` for emails
- Stream responses to frontend using SSE or chunked transfer

---

## 6. Environment Variables

```env
# backend/.env
ANTHROPIC_API_KEY=sk-ant-...
DATA_DIR=../data
PORT=8000

# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 7. Dependency Versions

### Backend (`requirements.txt`)
```
fastapi==0.111.0
uvicorn==0.29.0
pandas==2.2.2
anthropic==0.26.0
python-dotenv==1.0.1
pydantic==2.7.1
```

### Frontend (`package.json` key deps)
```json
{
  "next": "14.2.3",
  "react": "18.3.1",
  "tailwindcss": "3.4.3",
  "recharts": "2.12.7",
  "zustand": "4.5.2",
  "@anthropic-ai/sdk": "0.26.0",
  "lucide-react": "0.383.0"
}
```

---

## 8. Running Locally

```bash
# Terminal 1: Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm install
npm run dev

# App runs at http://localhost:3000
# API docs at http://localhost:8000/docs
```

---

## 9. Critical Engineering Rules

1. **Compute first, explain second.** All £ values come from pandas. Claude only narrates.
2. **Validate before display.** If validate.py fails, block the UI.
3. **Filter by date everywhere.** Every function accepts `as_of_date` for backtesting.
4. **No magic numbers.** Dead stock threshold (45 days), weekly sales floor (2 units) are config constants at top of `cash_engine.py`.
5. **Keep DataFrames in memory.** Load once on `/api/load-data`, store in app state (`app.state.dfs`).
6. **Test with a fixed date.** Use `2026-06-01` as "today" throughout — this is "today" in the dataset world.
