"""Shared config for the Khemera Market Intelligence pipeline."""
import os

# --- CBM business chain "pillars" this portal tags every item against ---
PILLARS = [
    "P1 Cement",
    "P2 Ready-Mixed Concrete",
    "P3 Building Materials",
    "P4 CBM-Adjacent",
    "Group",  # macro / company-wide items that don't map to one pillar
]

CATEGORIES = ["economy", "construct", "tourism", "regulation", "politics", "oil"]
SCOPES = ["Local", "World"]
IMPACTS = ["High", "Medium", "Low"]

# --- News sources the daily scraper pulls from ---
# `kind` tells scrape.py how to read the source:
#   "rss"   -> parse as an RSS/Atom feed
#   "html"  -> fetch the page and pull article links with a CSS selector
# `delay` overrides the default politeness pause (seconds) after fetching this source.
# Verified 2026-09-17 — see README "Known limitations" for sources that are skipped and why.
SOURCES = [
    {"name": "Khmer Times", "kind": "rss", "url": "https://www.khmertimeskh.com/feed/"},
    {"name": "Cambodianess", "kind": "html", "url": "https://cambodianess.com/",
     "selector": "h5 a, h3 a, article a"},
    {"name": "Kampuchea Thmey", "kind": "rss", "url": "https://kampucheathmey.com/feed", "delay": 10},
    {"name": "Construction & Property", "kind": "html", "url": "https://construction-property.com/all-news/",
     "selector": "article a, h2 a, h3 a"},
    {"name": "B2B Asia News", "kind": "html", "url": "https://b2b-asianews.com/business/news",
     "selector": "a h3, a h4, article a"},
    {"name": "Realestate.com.kh", "kind": "json_api",
     "url": "https://www.realestate.com.kh/api/blog/?page=1&page_size=10&show_content=true&strip_html=true&type=news"},
    {"name": "Open Development Cambodia", "kind": "html", "url": "https://opendevelopmentcambodia.net/news/",
     "selector": "h5 a, h3 a, article a"},
    {"name": "OilPrice.com", "kind": "rss", "url": "https://oilprice.com/rss/main"},
    {"name": "Ministry of Mines and Energy", "kind": "html", "url": "https://mme.gov.kh/newsroom",
     "selector": "article a, h2 a, h3 a"},
]
# NOT included, and why (see README "Known limitations" for details):
#   - Phnom Penh Post: blocks automated requests (HTTP 403 on every fetch, including robots.txt)
#   - Ministry of Commerce (moc.gov.kh): same 403 behavior, could not verify a safe fetch path
# Their stories are still picked up indirectly whenever Khmer Times / Kampuchea Thmey /
# Construction & Property report on the same news (as in the mockup).
#
# Checked against cambodia-news-sources.md (2026-09-17) and NOT added:
#   - Agence Kampuchea Presse (akp.gov.kh): no RSS feed found; page is JS-rendered so the
#     generic HTML extractor finds zero headline links. Would need a dedicated scraper.
#   - Reuters Energy: no working RSS endpoint found; Reuters actively blocks scrapers.
#   - U.S. EIA: publishes a data API (WTI/Brent benchmark prices), not a news feed — doesn't
#     fit this pipeline's title/url/snippet item schema.
#   - GlobalPetrolPrices.com Cambodia: a single weekly price snapshot page, not a list of
#     articles — same schema mismatch as EIA.
#   - Al Jazeera Economy / Xinhua English: RSS works, but only as global "all news" feeds
#     (no economy-specific feed exists) — adding them would flood the digest with mostly
#     non-Cambodia stories. Skipped to keep the feed relevant.
#   - Khmer Times — Property section: redundant with the main Khmer Times feed already above.

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
ARCHIVE_DIR = os.path.join(DATA_DIR, "archive")
DAILY_JSON = os.path.join(DATA_DIR, "daily.json")
WEEKLY_JSON = os.path.join(DATA_DIR, "weekly.json")
MONTHLY_JSON = os.path.join(DATA_DIR, "monthly.json")
SEEN_URLS_JSON = os.path.join(DATA_DIR, "seen_urls.json")

# How many days of daily items stay in data/daily.json (older ones remain in data/archive/*.json)
DAILY_WINDOW_DAYS = 14

# llama-3.3-70b-versatile returned 404 model_not_found for this account (likely gated
# behind an opt-in on some Groq accounts) — llama-3.1-8b-instant is available by default.
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
