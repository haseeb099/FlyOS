# FlyOS
**Commerce operating system for Pretty Fly — cash liberation in one surface**  
Wayflyer × Fin Hackathon · London · June 3–5, 2026

---

## "Pretty Fly has £18,200 stuck in hoodies and late POs. Here's how to get it back by Friday."

---

## What It Does

FlyOS ingests Pretty Fly's 24 months of DTC data and answers the one question they can't answer today:

> **Where is our cash stuck, and what do we do about it right now?**

In 3 seconds: ranked actions → evidence-backed detail → one-click email campaigns and CSV export.

---

## Quick Start

```bash
# 1. Clone / open this folder in Cursor
# 2. Copy Pretty Fly data into ./data/

# Terminal 1 — Backend
cd backend
pip install -r requirements.txt
cp .env.example .env   # Add your ANTHROPIC_API_KEY
uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend  
cd frontend
npm install
npm run dev

# Open http://localhost:3000
# Enter data path → validate → find cash leaks
```

---

## Build Order (Follow the Prompts)

| Prompt | What It Builds | When |
|--------|---------------|------|
| `PROMPT_01` | Data layer (pandas engine) | Day 1 morning |
| `PROMPT_02` | FastAPI server | Day 1 afternoon |
| `PROMPT_03` | Next.js frontend shell | Day 1 evening |
| `PROMPT_04` | Cash leaks polish | Day 2 morning |
| `PROMPT_05` | Backtest engine | Day 2 afternoon |
| `PROMPT_06` | LLM email + demo polish | Day 3 |

Each prompt in `prompts/` is designed to be pasted directly into Cursor Chat.
Do them in order. Don't skip ahead.

---

## Architecture

```
Pretty Fly CSVs (21 files)
        ↓
DataLoader → validate.py → 20 reconciliation checks
        ↓
cash_engine.py (pandas, no LLM)
        ↓
FastAPI (8000) ←→ Next.js (3000)
        ↓
Claude API (explanations + email copy only)
```

---

## Key Design Decisions

- **Pandas computes, Claude explains.** Numbers never touch the LLM.
- **Validate first, display second.** If reconciliation fails, the UI is blocked.
- **"Today" = 2026-06-01** throughout the dataset.
- **4 core tables** drive the cash computation: bank_transactions, inventory_movements, po_line_items, line_items.
- **Backtest = credibility.** Historical proof that the algorithm works.

---

## Docs

- [`docs/PRD.md`](docs/PRD.md) — Product requirements
- [`docs/TRD.md`](docs/TRD.md) — Technical requirements  
- [`docs/SE.md`](docs/SE.md) — Engineering spec
- [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) — Judge demo walkthrough

## Cursor Rules

- [`.cursor/rules/00-project.mdc`](.cursor/rules/00-project.mdc) — Always on
- [`.cursor/rules/01-data-layer.mdc`](.cursor/rules/01-data-layer.mdc) — Python data files
- [`.cursor/rules/02-api.mdc`](.cursor/rules/02-api.mdc) — FastAPI routes
- [`.cursor/rules/03-frontend.mdc`](.cursor/rules/03-frontend.mdc) — Next.js components
- [`.cursor/rules/04-llm.mdc`](.cursor/rules/04-llm.mdc) — Anthropic API calls

---

## Demo Narrative

> *"Pretty Fly has 24 months of perfect data. But they still can't answer: where is our cash stuck?*
> *We built FlyOS. It finds it in 3 seconds."*

1. Load data → 20 checks pass → "Validated ✓"
2. "Find Cash Leaks" → £18,200 across 14 items
3. Drill into Black Hoodie XL — £8,200 stuck, 60 days no sales
4. "Generate Email" → Claude writes the Klaviyo campaign
5. Backtest Feb 1 → "Grey Cap recommendation → 120 units cleared → £5,200 recovered"

Judge asks: "How confident are you in that number?"  
You say: "Run the validator yourself." Click. All 20 checks pass.

---

*Data is fictional. Built for Wayflyer × Fin Hackathon 2026.*
