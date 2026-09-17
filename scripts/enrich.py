"""Turns a raw scraped headline/snippet into the structured fields the portal displays,
using the Groq API (OpenAI-compatible chat completions)."""
import json
import os

from groq import Groq

from common import CATEGORIES, SCOPES, IMPACTS, PILLARS, GROQ_MODEL

SYSTEM_PROMPT = f"""You are a business-intelligence analyst for SCG Cambodia, a subsidiary of \
SCG Group (Thailand) that manufactures cement, ready-mixed concrete (RMC) and concrete roof \
tiles, and also imports/distributes building materials (ceramic roof tiles, sanitary ware, \
gypsum board, fiber cement board, steel, glass block, roof insulation, sealing tape, RMC \
admixture, engine lubricant, starch, Kubota machinery spare parts) and exports recycled paper.

You are given one raw news item (title + short snippet + source). Classify and summarize it \
for an internal daily intelligence feed read by SCG Cambodia's BD/executive team.

Respond with ONLY a JSON object, no other text, with exactly these fields:
- "category": one of {CATEGORIES}
- "scope": one of {SCOPES} ("Local" = Cambodia-specific, "World" = regional/global)
- "impact": one of {IMPACTS} (High/Medium/Low relevance to SCG Cambodia's business)
- "title": a clean, concise headline (rewrite only if the original is unclear; keep facts exact)
- "summary": ONE paragraph (2-3 sentences), factual, neutral tone, no speculation
- "pillar": one of {PILLARS} (which CBM business chain this affects most)
- "analysis": ONE short paragraph titled implicitly as "what this means for CBM" — concrete, \
specific, written for an executive who will act on it (mention $ impact, timing, or a decision \
to make if the source material supports it; do not invent numbers not present in the source)

If the item has no real relevance to SCG Cambodia's business, set "impact" to "Low" and keep the \
analysis brief and honest (e.g. "Limited direct relevance to CBM operations.") rather than \
fabricating significance.
"""


def enrich_item(title: str, snippet: str, source: str, url: str) -> dict:
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    user_prompt = f"Source: {source}\nURL: {url}\nTitle: {title}\nSnippet: {snippet}"

    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        response_format={"type": "json_object"},
    )
    raw = resp.choices[0].message.content
    data = json.loads(raw)

    # Guard rails: fall back to safe defaults if the model returns something unexpected
    data["category"] = data.get("category") if data.get("category") in CATEGORIES else "economy"
    data["scope"] = data.get("scope") if data.get("scope") in SCOPES else "Local"
    data["impact"] = data.get("impact") if data.get("impact") in IMPACTS else "Medium"
    data["pillar"] = data.get("pillar") if data.get("pillar") in PILLARS else "Group"
    data["title"] = data.get("title") or title
    data["summary"] = data.get("summary") or snippet
    data["analysis"] = data.get("analysis") or "Analysis unavailable for this item."
    data["source"] = source
    data["url"] = url
    return data
