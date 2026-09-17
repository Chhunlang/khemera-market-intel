"""Regenerates data/weekly.json and data/monthly.json from the accumulated daily archive.

Run on a schedule by .github/workflows/weekly-monthly.yml (weekly job runs every Monday,
monthly job runs on the 1st of each month — see that workflow for the cron rules).

Selection logic ("only significant items"): every item counts toward the stats, but only
High/Medium-impact items are summarized into bullets/narrative — Low-impact routine items
are counted, not narrated, matching the mockup's behavior.
"""
import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from collections import defaultdict

from common import ARCHIVE_DIR, WEEKLY_JSON, MONTHLY_JSON
from summarize import summarize_category, write_monthly_headline, CATEGORY_LABELS

ICT = timezone(timedelta(hours=7))


def load_items_since(start: datetime) -> list[dict]:
    items = []
    if not os.path.isdir(ARCHIVE_DIR):
        return items
    for fname in sorted(os.listdir(ARCHIVE_DIR)):
        if not fname.endswith(".json"):
            continue
        try:
            file_date = datetime.strptime(fname[:-5], "%Y-%m-%d").replace(tzinfo=ICT)
        except ValueError:
            continue
        if file_date >= start:
            with open(os.path.join(ARCHIVE_DIR, fname), "r", encoding="utf-8") as f:
                items.extend(json.load(f))
    return items


def compute_stats(items: list[dict]) -> dict:
    high = [it for it in items if it["impact"] == "High"]
    medium = [it for it in items if it["impact"] == "Medium"]
    local = [it for it in items if it["scope"] == "Local"]
    world = [it for it in items if it["scope"] == "World"]

    def breakdown(subset):
        counts = defaultdict(int)
        for it in subset:
            counts[it["category"]] += 1
        parts = sorted(counts.items(), key=lambda kv: -kv[1])
        return " · ".join(f"{n} {CATEGORY_LABELS.get(k, k).lower()}" for k, n in parts)

    total = len(items) or 1
    return {
        "total_items": len(items),
        "high_impact_count": len(high),
        "high_impact_breakdown": breakdown(high),
        "medium_impact_count": len(medium),
        "local_count": len(local),
        "world_count": len(world),
        "local_pct": round(100 * len(local) / total),
    }


def build_category_cards(items: list[dict]) -> list[dict]:
    by_cat = defaultdict(list)
    for it in items:
        by_cat[it["category"]].append(it)

    cards = []
    for cat_key, cat_items in by_cat.items():
        significant = [it for it in cat_items if it["impact"] in ("High", "Medium")]
        if not significant:
            continue  # nothing worth narrating for this category this period
        result = summarize_category(cat_key, significant)
        high_count = sum(1 for it in cat_items if it["impact"] == "High")
        cards.append(
            {
                "cat": CATEGORY_LABELS.get(cat_key, cat_key),
                "key": cat_key,
                "impact_label": "High impact" if high_count else "Medium impact",
                "summary": result["summary"],
                "bullets": result["bullets"],
            }
        )
    return cards


def build_weekly(now: datetime):
    start = now - timedelta(days=7)
    items = load_items_since(start)
    week_number = now.isocalendar()[1]
    data = {
        "generated_at": now.isoformat(),
        "period_label": f"{start.strftime('%d %b')} – {now.strftime('%d %b %Y')}",
        "week_number": week_number,
        "stats": compute_stats(items),
        "categories": build_category_cards(items),
    }
    os.makedirs(os.path.dirname(WEEKLY_JSON), exist_ok=True)
    with open(WEEKLY_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[weekly] wrote {WEEKLY_JSON} with {len(items)} items, {len(data['categories'])} cards")


def build_monthly(now: datetime):
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    items = load_items_since(start)
    stats = compute_stats(items)
    high_items = [it for it in items if it["impact"] == "High"]
    period_label = now.strftime("%B %Y")
    narrative = write_monthly_headline(period_label, high_items) if high_items else {
        "headline": period_label,
        "subhead": "No high-impact items recorded this month.",
    }
    data = {
        "generated_at": now.isoformat(),
        "period_label": period_label,
        "headline": narrative["headline"],
        "subhead": narrative["subhead"],
        "kpis": [
            {"label": "Items reviewed", "value": str(stats["total_items"])},
            {"label": "High impact", "value": str(stats["high_impact_count"])},
            {"label": "Local vs World", "value": f"{stats['local_count']} / {stats['world_count']}"},
            {"label": "Locally sourced", "value": f"{stats['local_pct']}%"},
        ],
        "categories": build_category_cards(items),
    }
    os.makedirs(os.path.dirname(MONTHLY_JSON), exist_ok=True)
    with open(MONTHLY_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[monthly] wrote {MONTHLY_JSON} with {len(items)} items, {len(data['categories'])} cards")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--period", choices=["weekly", "monthly"], required=True)
    args = parser.parse_args()

    now = datetime.now(ICT)
    if args.period == "weekly":
        build_weekly(now)
    else:
        build_monthly(now)
