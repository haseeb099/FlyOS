# PROMPT_05 — Backtest Engine
**Day 2 afternoon — the killer demo feature**

---

The backtest is what separates CashFly from a dashboard. It proves the algorithm works
by showing: "We recommended this in February. They could have done it. Here's what happened."

## 1. Backend: Complete the Backtest Route

In `backend/main.py`, the `/api/backtest` route should:

```python
@app.get("/api/backtest")
async def backtest(date: str, request: Request):
    dfs = request.app.state.dfs
    as_of = date.fromisoformat(date)
    
    # Step 1: Run algorithm on historical snapshot
    historical_leaks = run_full_leak_algorithm(dfs, as_of_date=as_of)
    
    # Step 2: Compute what actually happened in next 30 days
    thirty_days_later = as_of + timedelta(days=30)
    actual_outcomes = compute_actual_outcomes(dfs, historical_leaks, as_of, thirty_days_later)
    
    # Step 3: Estimate cash recovered IF recommendations were followed
    estimated_recovery = estimate_recovery(historical_leaks, actual_outcomes)
    
    return BacktestResult(
        as_of_date=str(as_of),
        recommendations=historical_leaks,
        actual_outcome_summary=actual_outcomes["summary"],
        estimated_cash_recovered_gbp=estimated_recovery
    )
```

In `cash_engine.py`, add:
```python
def compute_actual_outcomes(dfs, recommendations, from_date, to_date) -> dict:
    """
    For each recommended item, check what actually happened between from_date and to_date.
    For dead inventory items: how many units were actually sold?
    For POs: was the PO eventually delivered or cancelled?
    For ad campaigns: did they continue spending? Any conversions?
    
    Returns: {
        "by_item": [...],
        "summary": "str plain English summary",
        "total_units_moved": int,
        "total_revenue_recovered": float
    }
    """
```

## 2. Frontend: `BacktestTimeline.tsx` (full implementation)

Layout:
```
[Date Picker: "Pick a historical date to test"]  [Run Backtest]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  WHAT WE WOULD HAVE SAID          WHAT ACTUALLY HAPPENED
  (on Feb 1, 2026)                 (in the 30 days after)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  📦 Grey Cap (M) — £4,200         → 120 units sold
     "Clear this stock"             → £5,800 revenue
  
  📢 Winter Campaign — £800         → Campaign paused week 2
     "Pause — 0 conversions"        → £0 further waste

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ESTIMATED RECOVERY IF FOLLOWED:  £5,200
  (based on actual data from the 30 days after)
```

Colors:
- Left column: zinc/dark
- Right column: slightly lighter with green left border
- Recovery number: large amber

## 3. Pre-compute the "Good" Backtest Date

Before the demo, find the best backtest date to use:
Add a helper in `cash_engine.py`:

```python
def find_best_backtest_date(dfs) -> str:
    """
    Scan monthly intervals from 2024-09 to 2026-03.
    For each date, run the algorithm, then check the 30-day outcome.
    Return the date with highest actual_cash_recovered.
    Print a table of all dates + outcomes.
    """
```

Run this as a script: `python -c "from cash_engine import *; find_best_backtest_date(load_all_dfs('../data'))"`.

Use the output to hardcode the demo date. Present this date confidently in the demo:
> "On [DATE], CashFly would have flagged [X]. Here's what actually happened."

## 4. Loading State

The backtest can take 2-3 seconds. Show a progress message:
```typescript
const messages = [
  "Rewinding to " + selectedDate + "...",
  "Running cash leak algorithm on historical snapshot...",
  "Checking what actually happened...",
  "Computing recovery estimate..."
]
// Cycle through messages every 600ms while loading
```

## 5. Edge Case Handling

- Date too recent (< 30 days before dataset end): show warning "Need 30 days of outcome data"
- Date before dataset start: block with error
- No leaks found on historical date: show "No significant cash leaks detected on this date"
- Recommendation items that were NOT acted on: show "Not actioned — £X still stuck"

**When done:** Run backtest on three different dates and paste the estimated_cash_recovered values here. We'll pick the most compelling one for the demo.
