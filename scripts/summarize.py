"""Groq calls used to turn a pile of daily items into weekly/monthly executive narrative.
All numbers (counts, splits, percentages) are computed in Python from real data, never by
the model — Groq is only used to WRITE the prose around numbers we already know are true."""
import json
import os

from groq import Groq

from common import GROQ_MODEL

CATEGORY_LABELS = {
    "economy": "Economy",
    "construct": "Construction & Real Estate",
    "tourism": "Tourism",
    "regulation": "Regulation",
    "politics": "Politics",
    "oil": "Oil & Energy",
}


def _client() -> Groq:
    return Groq(api_key=os.environ["GROQ_API_KEY"])


def summarize_category(category_key: str, items: list[dict]) -> dict:
    """One category's roll-up for a weekly/monthly card: a short summary paragraph plus
    a handful of bullet points, each tied to a specific real item."""
    label = CATEGORY_LABELS.get(category_key, category_key)
    item_lines = "\n".join(
        f"- [{it['impact']}] {it['title']} (source: {it['source']}) — {it['summary']}"
        for it in items
    )
    prompt = f"""These are real news items tagged "{label}" for SCG Cambodia's period roll-up. \
Write:
1. "summary": ONE short paragraph (2 sentences) synthesizing the period's {label} news for an \
executive reader — trend-level, not a list.
2. "bullets": up to 4 bullet points, ONLY for the most significant items (skip Low-impact or \
routine ones). Each bullet is one sentence and MUST be grounded in the item text given — do not \
invent facts. Include which source each bullet is from.

Items:
{item_lines}

Respond as ONLY a JSON object: {{"summary": "...", "bullets": [{{"t": "...", "src": "..."}}]}}
"""
    resp = _client().chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        response_format={"type": "json_object"},
    )
    data = json.loads(resp.choices[0].message.content)
    data.setdefault("summary", "")
    data.setdefault("bullets", [])
    return data


def write_monthly_headline(period_label: str, high_impact_items: list[dict]) -> dict:
    """The big narrative headline + subhead for the Monthly Executive view."""
    item_lines = "\n".join(
        f"- [{it['category']}/{it['impact']}] {it['title']} — {it['analysis']}"
        for it in high_impact_items
    )
    prompt = f"""You are writing the opening headline of SCG Cambodia's Monthly Executive \
Summary for {period_label}, based ONLY on these real high-impact items from the month:

{item_lines}

Respond as ONLY a JSON object with:
- "headline": a punchy, specific headline under 12 words capturing the month's dominant theme \
for SCG Cambodia's business (cement/RMC/building materials/recycled paper)
- "subhead": 2-3 sentences: what happened this month and a one-line strategic recommendation \
for the quarter ahead. Ground every claim in the items given — no invented statistics.
"""
    resp = _client().chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        response_format={"type": "json_object"},
    )
    data = json.loads(resp.choices[0].message.content)
    data.setdefault("headline", period_label)
    data.setdefault("subhead", "")
    return data
