# PROMPT_06 — LLM Email Draft + Demo Polish
**Day 3 — final polish, the "wow" moment**

---

The core is working. Now add the LLM email feature and tighten the demo.

## 1. Email Generation (Streaming)

### Backend (`llm_service.py`)

```python
async def generate_email_campaign(
    variant_title: str,
    sku: str, 
    units: int,
    cash_tied_gbp: float,
    related_products: list[str],  # Products frequently bought together
    open_rate: float,              # From email_events table for this segment
    historical_lift: float,        # From discount_codes: avg revenue lift % when discounted
) -> AsyncIterator[str]:
    
    prompt = f"""Generate a promotional email campaign for Pretty Fly (London streetwear brand).

Dead stock to clear:
- Product: {variant_title} (SKU: {sku})
- Units available: {units}  
- Cash tied up: £{cash_tied_gbp:,.0f}
- Suggested discount: based on historical lift of {historical_lift:.0%} from discount codes

Target audience: customers who bought a complementary product ({', '.join(related_products[:3])}) but NOT {variant_title}.
Historical open rate for this segment: {open_rate:.0%}.

Return ONLY a JSON object:
{{
  "subject": "...",
  "preview_text": "...", 
  "body_paragraphs": ["...", "...", "..."],
  "cta_text": "...",
  "discount_code": "CLEAR[FIRST4OFSKU]20"
}}"""
    
    async with client.messages.stream(
        model="claude-sonnet-4-20250514",
        max_tokens=400,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        async for text in stream.text_stream:
            yield text
```

### Finding Related Products

Before calling LLM, compute in Python:
```python
def find_frequently_bought_with(variant_id, line_items, variants, products, top_n=3) -> list[str]:
    """Find products most frequently ordered in the same order as variant_id."""
    # Get orders containing this variant
    # Find other variants in those same orders
    # Return top N by co-occurrence count
```

### Historical Lift from Discount Codes
```python
def compute_discount_lift(discount_codes, orders, line_items) -> float:
    """
    Compare avg order value with discount applied vs without.
    Return as percentage lift: 0.15 means 15% higher AOV with discount.
    """
```

## 2. `EmailPreview.tsx` (complete implementation)

```tsx
export function EmailPreview({ leakId, variantTitle, units, cashTied, sku }: Props) {
  const [streaming, setStreaming] = useState(false)
  const [rawJson, setRawJson] = useState("")
  const [parsed, setParsed] = useState<EmailDraft | null>(null)
  
  const generate = async () => {
    setStreaming(true)
    const res = await fetch(`${API}/api/generate-email`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ leak_id: leakId, variant_title: variantTitle, units, cash_tied: cashTied, sku })
    })
    
    const reader = res.body!.getReader()
    let accumulated = ""
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      accumulated += new TextDecoder().decode(value)
      setRawJson(accumulated)
      
      // Try to parse progressively
      try {
        const clean = accumulated.replace(/```json|```/g, "").trim()
        setParsed(JSON.parse(clean))
      } catch {} // Still streaming — ignore parse errors
    }
    setStreaming(false)
  }
  
  return (
    <div className="bg-[#111] border border-[#222] rounded-xl p-6 space-y-4">
      {/* Mock email client chrome */}
      <div className="flex gap-2 mb-4">
        <div className="w-3 h-3 rounded-full bg-red-500"/>
        <div className="w-3 h-3 rounded-full bg-amber-500"/>
        <div className="w-3 h-3 rounded-full bg-green-500"/>
      </div>
      
      {!parsed && !streaming && (
        <button onClick={generate} className="w-full bg-amber-500 text-black font-bold py-3 rounded-lg">
          Generate Email Campaign →
        </button>
      )}
      
      {streaming && <div className="text-amber-400 animate-pulse">Writing email copy...</div>}
      
      {parsed && (
        <>
          <div className="space-y-2">
            <div className="text-xs text-zinc-500 uppercase tracking-wider">Subject</div>
            <div className="text-white font-medium">{parsed.subject}</div>
          </div>
          <div className="space-y-2">
            <div className="text-xs text-zinc-500 uppercase tracking-wider">Preview</div>
            <div className="text-zinc-400 text-sm">{parsed.preview_text}</div>
          </div>
          <div className="border-t border-[#222] pt-4 space-y-3">
            {parsed.body_paragraphs.map((p, i) => (
              <p key={i} className="text-zinc-300 text-sm leading-relaxed">{p}</p>
            ))}
          </div>
          <div className="bg-amber-500 text-black text-center py-2 rounded font-bold text-sm">
            {parsed.cta_text} — Use code {parsed.discount_code}
          </div>
          <div className="flex gap-3 pt-2">
            <button onClick={() => navigator.clipboard.writeText(JSON.stringify(parsed, null, 2))}
                    className="text-xs text-zinc-400 hover:text-white border border-[#333] px-3 py-1.5 rounded">
              Copy JSON
            </button>
            <button className="text-xs text-zinc-400 hover:text-white border border-[#333] px-3 py-1.5 rounded">
              Download Customer CSV
            </button>
          </div>
        </>
      )}
    </div>
  )
}
```

## 3. Demo Script Rehearsal

Add a hidden `/demo` route that auto-runs the three demo scenarios in sequence:
- Click "Scenario 1" → highlights the dead hoodie LeakCard
- Click "Scenario 2" → highlights the late PO
- Click "Scenario 3" → highlights ad waste
- Click "Backtest" → jumps to backtest with best date pre-selected
- Click "Email" → opens email generator for Scenario 1 item

This is your presentation remote control.

## 4. Final Pre-Demo Checks

Before presenting:

```bash
# 1. Confirm validator passes
cd backend && python -c "from data_loader import DataLoader; r = DataLoader('../data').load(); print(r['validation'])"

# 2. Confirm cash leaks returns data
curl http://localhost:8000/api/cash-leaks | python -m json.tool | head -50

# 3. Confirm backtest works on your chosen demo date
curl "http://localhost:8000/api/backtest?date=YYYY-MM-DD" | python -m json.tool

# 4. Confirm email generation streams
curl -X POST http://localhost:8000/api/generate-email \
  -H "Content-Type: application/json" \
  -d '{"leak_id":"1","variant_title":"Heritage Hoodie XL","units":340,"cash_tied":8200,"sku":"HH-BLK-XL"}'
```

## 5. The "£18,200" Moment

In `CashMeter.tsx`, add this exact line under the number:
```tsx
<p className="text-zinc-400 text-sm mt-2">
  Across {leakCount} items · Recoverable by 30 Jun 2026
</p>
```

The judge asks: "How confident are you in that number?"
You say: "All 20 reconciliation checks pass. Bank transactions → COGS → inventory — every number traces. Run the validator yourself."
Then click "Show Reconciliation" to reveal the proof panel.

**You're ready to demo. Ship it.**
