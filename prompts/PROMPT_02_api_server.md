# PROMPT_02 — FastAPI Server
**Paste into Cursor Chat after PROMPT_01 is working**

---

Read `.cursor/rules/02-api.mdc` before writing any code.

The data layer (`cash_engine.py`, `data_loader.py`, `models.py`) is complete and tested.
Now build the complete FastAPI server in `backend/main.py`.

## Requirements

### App Setup
- FastAPI with lifespan context manager
- CORS: allow `http://localhost:3000`
- App state: `app.state.dfs = {}`, `app.state.validated = False`
- Global exception handler that returns `{"error": str(exc)}` with status 500

### Routes

**POST `/api/load-data`**
- Body: `{"data_path": str}`
- Calls `DataLoader(data_path).load()`
- Sets `app.state.dfs` and `app.state.validated`
- Returns `LoadDataResponse` with validation summary

**GET `/api/health`**
- Always responds (no data guard)
- Returns `{"status": "ok", "validated": bool, "files_loaded": int}`

**GET `/api/cash-position`**
- Guard: data must be loaded
- Reads `bank_transactions` to get latest balance
- Returns `CashPosition` model

**GET `/api/cash-leaks`**
- Query param: `as_of_date: str = "2026-06-01"`
- Guard: data must be loaded
- Calls `find_dead_inventory`, `find_late_pos`, `find_ad_waste`
- Converts results to `list[CashLeak]`
- Calls `compute_cash_liberation_total`
- Returns `CashLeaksResponse`
  
For each dead inventory row → `CashLeak(category="inventory", ...)`
For each late PO row → `CashLeak(category="supplier_po", ...)`
For each ad waste row → `CashLeak(category="ad_spend", ...)`
Sort combined list by `cash_at_risk_gbp` descending.

**GET `/api/backtest`**
- Query param: `date: str` (required)
- Guard: data must be loaded
- Run full cash leaks pipeline with `as_of_date = parse(date)`
- Additionally: compute what actually happened in 30 days AFTER `date`
  (actual units sold of the flagged variants, actual cash recovered)
- Returns `BacktestResult`

**POST `/api/generate-email`**
- Body: `{"leak_id": str, "variant_title": str, "units": int, "cash_tied": float, "sku": str}`
- Returns `StreamingResponse` (SSE) from `llm_service.generate_email_campaign()`
- Content-type: `text/event-stream`

### `backend/llm_service.py`
Create this file with:
```python
async def explain_leak(leak_data: dict) -> str
async def generate_email_campaign(variant_title, units, cash_tied, sku) -> AsyncIterator[str]
```
Use the exact system prompt and user prompt patterns from `.cursor/rules/04-llm.mdc`.
Load `ANTHROPIC_API_KEY` from environment via `python-dotenv`.

### `backend/requirements.txt`
```
fastapi==0.111.0
uvicorn==0.29.0
pandas==2.2.2
anthropic==0.26.0
python-dotenv==1.0.1
pydantic==2.7.1
```

**When done:** Test every endpoint with `curl` commands:
```bash
curl -X POST http://localhost:8000/api/load-data -H "Content-Type: application/json" -d '{"data_path": "../data"}'
curl http://localhost:8000/api/cash-leaks
curl "http://localhost:8000/api/backtest?date=2026-02-01"
```
Paste the `cash-leaks` response here before moving to PROMPT_03.
