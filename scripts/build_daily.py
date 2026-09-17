"""Daily job: scrape sources, enrich new items with Groq, update data/daily.json
and today's archive file. Run once a day by .github/workflows/daily.yml."""
import json
import os
import re
from datetime import datetime, timezone, timedelta

from common import (
    ARCHIVE_DIR,
    DAILY_JSON,
    DAILY_WINDOW_DAYS,
    DATA_DIR,
    SEEN_URLS_JSON,
)
from enrich import enrich_item
from scrape import fetch_all

ICT = timezone(timedelta(hours=7))  # Cambodia time


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:60]


def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    now = datetime.now(ICT)
    today_str = now.strftime("%Y-%m-%d")
    archive_path = os.path.join(ARCHIVE_DIR, f"{today_str}.json")

    seen_urls = set(load_json(SEEN_URLS_JSON, []))
    todays_items = load_json(archive_path, [])

    raw_items = fetch_all()
    new_raw = [it for it in raw_items if it["url"] not in seen_urls]
    print(f"[build_daily] {len(raw_items)} scraped, {len(new_raw)} new")

    for raw in new_raw:
        try:
            enriched = enrich_item(raw["title"], raw["snippet"], raw["source"], raw["url"])
        except Exception as exc:  # noqa: BLE001 - one bad item must not kill the run
            print(f"[build_daily] enrich FAILED for {raw['url']}: {exc}")
            continue

        enriched["id"] = f"{today_str}-{slugify(enriched['title'])}"
        enriched["date"] = today_str
        enriched["time"] = now.strftime("%H:%M")
        todays_items.append(enriched)
        seen_urls.add(raw["url"])
        print(f"[build_daily] added: {enriched['title'][:70]}")

    save_json(archive_path, todays_items)
    save_json(SEEN_URLS_JSON, sorted(seen_urls)[-5000:])  # cap growth

    # Rebuild the rolling daily.json window from the last N archive files
    window_items = []
    cutoff = now - timedelta(days=DAILY_WINDOW_DAYS)
    for fname in sorted(os.listdir(ARCHIVE_DIR)):
        if not fname.endswith(".json"):
            continue
        try:
            file_date = datetime.strptime(fname[:-5], "%Y-%m-%d").replace(tzinfo=ICT)
        except ValueError:
            continue
        if file_date >= cutoff:
            window_items.extend(load_json(os.path.join(ARCHIVE_DIR, fname), []))

    window_items.sort(key=lambda it: (it["date"], it["time"]), reverse=True)
    save_json(DAILY_JSON, {"generated_at": now.isoformat(), "items": window_items})
    print(f"[build_daily] daily.json now has {len(window_items)} items")


if __name__ == "__main__":
    main()
