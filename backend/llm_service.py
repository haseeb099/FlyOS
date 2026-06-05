"""Claude API for explanations and email copy only — numbers come from pandas."""

from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator
from typing import Any

from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are a DTC finance analyst for Pretty Fly, a London streetwear brand selling premium hoodies, tees, sweatpants, caps, and trainers.

You write concise, plain-English explanations and email marketing copy.

Rules:
- Never invent numbers. Only use the exact figures provided in the user message.
- Be direct. No filler phrases like "certainly" or "great question".
- Max 3 sentences for explanations.
- Email copy: punchy, brand-appropriate, not corporate.
- Pretty Fly tone: confident, London streetwear, not luxury, not fast fashion.
"""

MODEL = "claude-sonnet-4-20250514"


def _client() -> Any:
    try:
        import anthropic
    except ImportError:
        return None

    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key or api_key.startswith("sk-ant-your"):
        return None
    return anthropic.AsyncAnthropic(api_key=api_key)


async def generate_briefing_narrative(facts: dict[str, Any]) -> AsyncIterator[str]:
    """Stream executive briefing narrative from pre-computed facts only."""
    user_prompt = f"""Write a morning executive briefing for Pretty Fly's founder.

Use ONLY these pre-computed facts — do not invent any £ amounts or counts:

{json.dumps(facts, indent=2)}

Format:
- Opening paragraph: cash position snapshot (2 sentences)
- "Top risks" section: 3 bullet points referencing the exact amounts provided
- "Opportunities" section: 3 bullet points with exact recoverable amounts
- Closing: one sentence call to action for this week

Tone: direct, finance-savvy, London DTC. No fluff. Max 250 words total."""

    client = _client()
    fallback = (
        f"As of {facts.get('as_of_date', 'today')}, net cash is "
        f"£{facts.get('net_cash_gbp', 0):,.0f} with "
        f"£{facts.get('total_liberation_gbp', 0):,.0f} recoverable across inventory, "
        f"supplier POs, and ad spend. Review the top three risks and opportunities "
        f"in the Action Center this morning."
    )

    if client is None:
        yield f"data: {json.dumps({'text': fallback})}\n\n"
        return

    try:
        async with client.messages.stream(
            model=MODEL,
            max_tokens=600,
            temperature=0.4,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        ) as stream:
            async for text in stream.text_stream:
                yield f"data: {json.dumps({'text': text})}\n\n"
    except Exception:
        yield f"data: {json.dumps({'text': fallback})}\n\n"


async def explain_leak_for_api(leak: dict[str, Any]) -> str:
    """Return a short plain-English explanation of a cash leak."""
    import re

    variant_title = leak.get("variant_title", leak.get("title", "Product"))
    sku = leak.get("sku", leak.get("subtitle", ""))
    units_or_days = str(leak.get("units_or_days", ""))

    units = int(leak.get("units", leak.get("current_stock_units", 0)))
    if units == 0:
        unit_match = re.search(r"(\d+)\s*units?", units_or_days, re.IGNORECASE)
        if unit_match:
            units = int(unit_match.group(1))

    cash_tied = float(
        leak.get("cash_tied", leak.get("cash_at_risk_gbp", leak.get("recoverable_gbp", 0)))
    )
    days_stagnant = int(leak.get("days_stagnant", leak.get("days_of_stock", 0)))
    if days_stagnant == 0:
        day_match = re.search(r"(\d+)\s*days?", units_or_days, re.IGNORECASE)
        if day_match:
            days_stagnant = int(day_match.group(1))

    weekly_sales = float(leak.get("weekly_sales", 0))
    category = leak.get("category", "inventory")
    recommended = leak.get("recommended_action", "")

    if category != "inventory":
        user_prompt = f"""Cash leak alert:
Category: {category}
Title: {variant_title}
Detail: {sku}
Cash at risk: £{cash_tied:,.0f}
Recommended action: {recommended}

In 2-3 sentences, explain why this is urgent for Pretty Fly's cash position."""
    else:
        user_prompt = f"""Dead stock alert:
Product: {variant_title} ({sku})
Units in warehouse: {units}
Days since last meaningful sale: {days_stagnant}
Cash tied up (at landed cost): £{cash_tied:,.0f}
Average weekly sales last month: {weekly_sales:.1f} units

In 2-3 sentences, explain why this is a cash risk for Pretty Fly and what the urgency is."""

    client = _client()
    if client is None:
        return (
            f"£{cash_tied:,.0f} is tied up in {units} units of {variant_title} "
            f"with ~{days_stagnant} days of stock on hand — cash better used elsewhere."
        )

    try:
        response = await client.messages.create(
            model=MODEL,
            max_tokens=200,
            temperature=0.3,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        block = response.content[0]
        return block.text if hasattr(block, "text") else str(block)
    except Exception:
        return (
            f"£{cash_tied:,.0f} is tied up in {units} units of {variant_title} "
            f"with slow sell-through — act this week to free working capital."
        )


async def generate_email_campaign(
    variant_title: str,
    units: int,
    cash_tied: float,
    sku: str = "",
    *,
    discount_pct: int = 20,
    open_rate: float = 0.42,
    related_product: str = "hoodies",
) -> AsyncIterator[str]:
    """Stream SSE chunks for promotional email copy."""
    user_prompt = f"""Generate a promotional email campaign to move dead stock.

Product: {variant_title}
SKU: {sku}
Units to clear: {units}
Suggested discount: {discount_pct}% (based on historical lift data)
Target audience: customers who bought {related_product} in the last 6 months
Historical email open rate for this segment: {open_rate:.0%}
Cash tied at landed cost: £{cash_tied:,.0f}

Return ONLY a JSON object with these exact keys:
{{
  "subject": "email subject line (max 60 chars)",
  "preview_text": "preview text (max 90 chars)",
  "body": "email body (3-4 paragraphs, plain text, no HTML)",
  "cta": "call to action button text (max 5 words)"
}}"""

    fallback = {
        "subject": f"{discount_pct}% off {variant_title} — ends Sunday",
        "preview_text": f"Clear {units} units sitting in the warehouse",
        "body": (
            f"We've got too many {variant_title} pieces on the shelf (£{cash_tied:,.0f} tied up).\n\n"
            f"Take {discount_pct}% off this weekend only — same quality, better price.\n\n"
            f"Tap below before your size goes."
        ),
        "cta": "Shop the drop",
    }

    client = _client()
    if client is None:
        yield f"data: {json.dumps(fallback)}\n\n"
        return

    try:
        async with client.messages.stream(
            model=MODEL,
            max_tokens=400,
            temperature=0.7,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        ) as stream:
            async for text in stream.text_stream:
                yield f"data: {text}\n\n"
    except Exception:
        yield f"data: {json.dumps(fallback)}\n\n"
