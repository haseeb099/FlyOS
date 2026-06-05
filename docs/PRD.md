# Product Requirements Document
# CashFly — "Find Your Stuck Cash in 3 Seconds"
**Version 1.0 | Hackathon Build | June 3–5, 2026**

---

## 1. Problem Statement

Pretty Fly is a London streetwear brand with 24 months of perfect data. Despite this, their team cannot answer the single most important operational question:

> **"Where is our cash actually stuck, and what do we do about it today?"**

They have cash tied up in slow-moving inventory, delayed supplier POs, and underperforming ad campaigns — but no unified tool to surface this. An accountant could find it in a week. CashFly finds it in 3 seconds.

---

## 2. Target User

**Primary:** Pretty Fly's founder / head of operations  
**Usage pattern:** Daily morning check-in, 5 minutes  
**Technical level:** Non-technical — needs plain English, not SQL

---

## 3. Core Value Proposition

> *"Pretty Fly has £18,000 stuck in hoodies and late POs. Here's exactly how to get it back by Friday."*

Not a dashboard. Not a chatbot. A **verifiable, cash-liberating action machine**.

---

## 4. Feature Scope (Hackathon MVP)

### MUST HAVE (Day 1–2)
| Feature | Description | Success Metric |
|---------|-------------|----------------|
| Data loader | Upload/mount data folder, validate, confirm reconciliation | All validate.py checks pass |
| Cash position | Current bank balance + outstanding payables + receivables | Matches bank_transactions within £1 |
| Dead inventory detector | Rank variants by cash tied up × days stagnant | Top 10 items with £ values |
| Late PO detector | POs past delivery date with prepaid amounts | Recoverable £ per PO |
| Cash leak summary | Total £ across all categories | Single headline number |

### SHOULD HAVE (Day 2–3)
| Feature | Description |
|---------|-------------|
| Backtest engine | Run algorithm on historical date, show outcome |
| LLM email draft | One-click email copy for dead stock campaign |
| Ad waste detector | Campaigns with spend and zero conversions last 7d |
| Export CSV | Customer list for dead stock email → Klaviyo upload |

### NICE TO HAVE (If time permits)
| Feature | Description |
|---------|-------------|
| Womenswear insight | Flag higher return rates / slower turns for Dec 2025 launch |
| Promotion simulator | "What if I discount 20%?" using historical lift from discount_codes |
| CFO weekly brief | Auto-generated narrative summary |

---

## 5. User Flows

### Flow 1: First Run
```
1. User opens app
2. Points app at data folder (or uploads)
3. App runs validate.py → shows "✓ All 20 reconciliation checks passed"
4. Dashboard loads with today's cash position
5. "3 cash leaks found. £18,200 recoverable." CTA button
```

### Flow 2: Daily Check
```
1. User opens app (data already loaded)
2. Dashboard shows: Cash position | Top 3 leaks | Days since last action
3. User clicks a leak → sees full detail + recommended action
4. User clicks "Generate Email" → LLM drafts campaign copy
5. User downloads CSV of target customers
```

### Flow 3: Backtest
```
1. User picks historical date (date picker)
2. App shows: "On Feb 1, we would have flagged these 3 items"
3. App shows: "In the 30 days after, here's what happened"
4. App shows: "Following the recommendation would have recovered £5,200"
```

---

## 6. UI Requirements

### Design Language
- Dark theme (Precision Dark — Linear/Vercel aesthetic)
- Amber accent (#F59E0B) — matches Pretty Fly brand
- Clean mono font for numbers (JetBrains Mono or similar)
- No decorative elements — every pixel earns its place

### Key UI Components
- **CashMeter**: Large number showing total recoverable cash (animated counter)
- **LeakCard**: Per-item card with icon (inventory/PO/ads), £ amount, action button
- **ReconciliationBadge**: Green "✓ Validated" or red "✗ Mismatch" in header
- **BacktestTimeline**: Before/after comparison with actual outcome
- **EmailPreview**: LLM-generated email in a mock inbox frame

### Layout
```
Header: [CashFly logo] [ReconciliationBadge] [Data: Pretty Fly · Jun 2026]

Hero: "£18,200 recoverable today"  [Find Cash Leaks →]

Tabs: [Overview] [Inventory] [Suppliers] [Ad Spend] [Backtest]

Footer: [Powered by Wayflyer × Fin Hackathon data]
```

---

## 7. Non-Requirements (Explicitly Out of Scope)

- No AI executive team / board meeting feature
- No What-If simulator (too risky for 3 days)
- No real-time API connections (snapshot data only)
- No multi-user auth
- No database (everything in-memory)
- No mobile optimization (desktop demo only)

---

## 8. Judging Criteria Alignment

| Criterion | How CashFly Delivers |
|-----------|----------------------|
| **Execution (Does it work?)** | Fewer than 5 tables in core flow; validate.py proves reconciliation; no faked data |
| **Business value (Would they pay?)** | Answers the #1 unanswered question from the README; backtest proves ROI |
| **Demo quality (Compelling?)** | 3-second "Find Cash Leaks" → specific £ numbers → one-click email draft |

---

## 9. Demo Script (Rehearse This)

> *"Pretty Fly has 24 months of perfect data. But they still can't answer: where is our cash stuck? We built CashFly. It finds it in 3 seconds."*

**[Load data → Validate ✓]**
> *"First, we prove the numbers are real. All 20 reconciliation checks pass."*

**[Click "Find Cash Leaks"]**
> *"Three cash leaks. £18,200 total."*

**[Show Leak 1: Black Hoodie XL]**
> *"340 units. 60 days no significant sales. £8,200 in landed cost sitting in a warehouse."*

**[Click "Generate Email"]**
> *"One click. CashFly drafts a targeted email to 1,200 customers who bought the matching hoodie but not the jogger. Subject line, body, discount code — ready to upload to Klaviyo."*

**[Show Backtest]**
> *"Does this actually work? We ran it on February 1st. It flagged the Grey Cap bundle. Pretty Fly did it. They cleared 120 units and recovered £5,200 in March. The data proves it."*

**[Show Total]**
> *"£18,200. Recoverable by end of June. Implementation: 1 hour a week."*

---

## 10. Success Definition

The demo is a success if a judge says: *"Could Pretty Fly actually use this tomorrow?"*  
The answer must be yes, with a working CSV export to prove it.
