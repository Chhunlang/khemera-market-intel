"""Pulls recent headlines from each configured source.

RSS sources are parsed directly. HTML sources use a best-effort generic extractor
(looks for headline-shaped links) since not every site publishes a feed. If a
particular HTML source stops matching well, tighten its selector in common.py's
SOURCES list (add a "selector" key with a CSS selector for headline links) rather
than rewriting this file.
"""
import time

import feedparser
import requests
from bs4 import BeautifulSoup

from common import SOURCES

# Plain, transparent, non-AI reader UA. OilPrice.com's robots.txt explicitly blocks
# AI-crawler UA strings (ClaudeBot, GPTBot, CCBot, etc.) even though /rss/main itself
# is open to generic bots — so we identify as a normal feed reader, not an AI agent.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; KhemeraMarketIntelBot/1.0; "
    "+https://github.com/Chhunlang/khemera-market-intel; contact: chhunlac@scg.com)"
}
REQUEST_TIMEOUT = 20
MAX_ITEMS_PER_SOURCE = 12


def fetch_rss(source: dict) -> list[dict]:
    feed = feedparser.parse(source["url"], request_headers=HEADERS)
    items = []
    for entry in feed.entries[:MAX_ITEMS_PER_SOURCE]:
        title = getattr(entry, "title", "").strip()
        link = getattr(entry, "link", "").strip()
        snippet = getattr(entry, "summary", "") or getattr(entry, "description", "")
        snippet = BeautifulSoup(snippet, "html.parser").get_text(" ", strip=True)[:500]
        if title and link:
            items.append({"title": title, "url": link, "snippet": snippet, "source": source["name"]})
    return items


def fetch_json_api(source: dict) -> list[dict]:
    """For sites whose news listing is client-rendered (no usable static HTML) but that
    expose a plain JSON API their own front-end calls — e.g. realestate.com.kh is a Next.js
    app; its /news/ page embeds no server-rendered links, but its own __NEXT_DATA__ payload
    revealed the public /api/blog/ endpoint it fetches from, at the same URL/frequency a
    real visitor's browser would."""
    resp = requests.get(source["url"], headers=HEADERS, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    results = resp.json().get("results", [])
    items = []
    for r in results[:MAX_ITEMS_PER_SOURCE]:
        title = (r.get("title") or "").strip()
        slug = r.get("slug", "")
        if not title or not slug:
            continue
        url = f"https://www.realestate.com.kh/news/{slug}/"
        snippet = (r.get("content_en") or r.get("content") or "")[:500]
        items.append({"title": title, "url": url, "snippet": snippet, "source": source["name"]})
    return items


def fetch_html(source: dict) -> list[dict]:
    resp = requests.get(source["url"], headers=HEADERS, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    selector = source.get("selector", "article a, h1 a, h2 a, h3 a")
    seen_urls = set()
    items = []
    for a in soup.select(selector):
        title = a.get_text(" ", strip=True)
        href = a.get("href", "")
        if not title or len(title) < 20 or not href:
            continue
        if href.startswith("/"):
            href = source["url"].rstrip("/") + href
        if not href.startswith("http") or href in seen_urls:
            continue
        seen_urls.add(href)
        items.append({"title": title, "url": href, "snippet": "", "source": source["name"]})
        if len(items) >= MAX_ITEMS_PER_SOURCE:
            break
    return items


def fetch_all() -> list[dict]:
    all_items = []
    for source in SOURCES:
        try:
            if source["kind"] == "rss":
                found = fetch_rss(source)
            elif source["kind"] == "json_api":
                found = fetch_json_api(source)
            else:
                found = fetch_html(source)
            print(f"[scrape] {source['name']}: {len(found)} items")
            all_items.extend(found)
        except Exception as exc:  # noqa: BLE001 - one bad source must not kill the run
            print(f"[scrape] {source['name']} FAILED: {exc}")
        time.sleep(source.get("delay", 1.5))  # be polite between requests (per-source override)
    return all_items
