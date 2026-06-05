# FlyOS Demo Script
# Wayflyer × Fin Hackathon · June 2026
#
# Run backend (port 8000) and frontend (port 3000) before rehearsing.

## 1. Open FlyOS
- Navigate to http://localhost:3000
- If data not loaded: go to **Data** → Load `../pretty_fly_data_pack/data` → **Load & Validate**
- Confirm green **✓ Validated** badge (20/20 rules)

## 2. Action Center (home)
- Headline shows **full liberation total** (all dead stock + POs + ads — not top-10 sum)
- KPI strip: Recoverable · Net cash · Action count · Category breakdown
- Select **#1 inventory action** (e.g. Black Hoodie)
- Click **Why this matters** → LLM explanation streams
- Click **Draft Email** → Generate → **Download CSV** (real Klaviyo segment)

## 3. Supplier / Ad actions
- Select a **Supplier PO** action → **Chase Supplier** → see simulated impact + draft email
- Select an **Ad spend** action → **Pause Campaign** → see £ saved estimate
- **Mark done** → action greys out in queue (local state)

## 4. Executive Briefing
- Go to **Briefing**
- Review pre-computed Top 3 Risks and Top 3 Opportunities (£ from pandas)
- Click **Generate Morning Brief** → narrative streams (numbers injected only)

## 5. Backtest proof
- Go to **Backtest**
- Click **Best demo date** OR set date to **2026-02-01**
- Run backtest → see recommendations vs 30-day actual outcome
- Bar chart: recommended vs actual recovery by category

## 6. Judge challenge
- Click **Reconciliation badge** in sidebar
- Show validator output on **Data** page (structured rule failures if any)

## Talking points
> "You have £X tied up in three places. Here's how to free £Y by end of June."
> Every £ traces to a pandas join — click evidence tooltips to see source tables.
