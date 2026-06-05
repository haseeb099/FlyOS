# PROMPT_03 — Frontend Shell
**Paste into Cursor Chat after PROMPT_02 API is verified working**

---

Read `.cursor/rules/03-frontend.mdc` before writing any code.

The FastAPI backend is running on `http://localhost:8000`.
Now scaffold the complete Next.js 14 frontend.

## Setup
```bash
cd frontend
npx create-next-app@14 . --typescript --tailwind --eslint --app --src-dir=no --import-alias="@/*"
npm install zustand lucide-react recharts
npx shadcn-ui@latest init
npx shadcn-ui@latest add badge button card tabs
```

## Files to Create

### `frontend/lib/types.ts`
Define TypeScript interfaces matching the Pydantic models:
```typescript
interface CashLeak { id, category, title, subtitle, cash_at_risk_gbp, units_or_days, recommended_action, recoverable_gbp, confidence }
interface CashLeaksResponse { total_recoverable_gbp, leaks, validation_status, computed_at }
interface CashPosition { bank_balance_gbp, outstanding_payables_gbp, expected_receivables_gbp, net_cash_gbp, as_of_date }
interface BacktestResult { as_of_date, recommendations, actual_outcome_summary, estimated_cash_recovered_gbp }
```

### `frontend/lib/api.ts`
All fetch functions with proper error handling. Functions:
- `loadData(dataPath: string)`
- `getHealth()`
- `getCashPosition()`
- `getCashLeaks(asOfDate?: string)`
- `runBacktest(date: string)`
- `generateEmail(params: EmailParams): Response` (for streaming)

### `frontend/lib/store.ts`
Zustand store with:
- `isDataLoaded: boolean`
- `validationStatus: "pending" | "passed" | "failed"`
- `totalRecoverable: number`
- `leakCount: number`
- Actions: `setLoaded`, `setValidation`, `setCashSummary`

### `frontend/app/layout.tsx`
- Dark background `#0a0a0a`
- JetBrains Mono via Google Fonts (for number displays)
- Minimal header: "CashFly" + ReconciliationBadge + "Pretty Fly · Jun 2026"

### `frontend/app/page.tsx` (Dashboard)
Hero section:
- If data not loaded: show `<DataLoader />` component
- If data loaded: show `<CashMeter totalGbp={totalRecoverable} />` + top 3 `<LeakCard />` items
- CTA: "See All Cash Leaks →" links to `/leaks`

### `frontend/app/leaks/page.tsx`
- Tabs: All | Inventory | Suppliers | Ad Spend
- Full list of `<LeakCard />` items, sorted by `cash_at_risk_gbp`
- Each card has "Generate Email" or "Mark Actioned" button

### `frontend/app/backtest/page.tsx`
- Date picker (input type="date", min="2024-06-01", max="2026-04-01")
- On submit: call `/api/backtest?date=...`
- Show `<BacktestTimeline />` with before/after comparison

### `frontend/app/email/page.tsx`
- Dropdown to select a dead stock item
- "Generate Email" button
- `<EmailPreview />` showing streamed LLM output

## Components

### `components/DataLoader.tsx`
- Input field: "Path to data folder (e.g. /Users/you/pretty_fly_data_pack/data)"
- "Load & Validate" button
- Loading state with message "Running 20 reconciliation checks..."
- Success: green checkmark + "All checks passed. X files loaded."
- Failure: red X + list of failed checks

### `components/CashMeter.tsx`
- Animated counter: counts up from 0 to `totalGbp` over 2 seconds
- Large `font-mono text-6xl font-bold text-amber-400`
- Subtitle: "recoverable by end of June"
- `ReconciliationBadge` underneath

### `components/LeakCard.tsx`
Props: `leak: CashLeak, onAction: () => void`
- Category icon: 📦 inventory / 🏭 supplier / 📢 ads
- Category badge (amber/orange/blue)
- `cash_at_risk_gbp` in large amber mono font
- Subtitle and recommended action in muted text
- Action button (amber, full width on hover)

### `components/ReconciliationBadge.tsx`
- Green pill: "✓ Validated" when `validationStatus === "passed"`
- Red pill: "✗ Not Validated" otherwise

### `components/BacktestTimeline.tsx`
Props: `result: BacktestResult`
- Two-column grid
- Left: "What we recommended on [date]" — list of LeakCards
- Right: "What actually happened" — actual_outcome_summary text
- Bottom: Large amber number "£X recovered if followed"

### `components/EmailPreview.tsx`
Props: `onFetch: () => Response (streaming)`
- Mock email client frame (dark bg, lighter inner)
- Subject, Preview, Body fields
- Shows text streaming in real-time as chunks arrive
- "Copy All" and "Download CSV" buttons at bottom

## Styling Constants (`tailwind.config.ts`)
Extend colors:
```js
amber: { DEFAULT: "#F59E0B", dim: "#92400E" },
surface: { DEFAULT: "#111111", 2: "#1a1a1a" },
```

**When done:** Open `http://localhost:3000`, load data, and confirm the CashMeter shows a non-zero total. Take a screenshot and paste here.
