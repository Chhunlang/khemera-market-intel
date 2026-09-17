# Khemera Market Intelligence

An auto-updating internal news portal for SCG Cambodia's BD team. It watches Cambodian
business/construction/energy news daily, uses AI to tag and analyze each item for CBM's
business, and publishes a website that updates itself — no manual work required once set up.

## How it works (plain English)

1. **Every day at 08:00 Cambodia time**, a robot (`.github/workflows/daily.yml`) wakes up on
   GitHub's servers, reads the news sources listed in `scripts/common.py`, and finds new
   articles it hasn't seen before.
2. For each new article, it asks an AI (Groq) to write the same fields as the original mockup:
   category, scope, impact, a clean title, a one-paragraph summary, which CBM business line it
   affects, and a short "what this means for CBM" analysis.
3. Those results are saved into `data/daily.json` (and archived permanently in
   `data/archive/YYYY-MM-DD.json`).
4. **Every Monday**, a second robot (`.github/workflows/weekly-monthly.yml`) rolls up the past
   7 days into `data/weekly.json`. **On the 1st of every month**, it also rolls up the whole
   month into `data/monthly.json`. Only items rated High/Medium impact get written into the
   narrative — Low-impact items are still counted in the stats but not narrated, same as the
   original mockup's behavior.
5. Any time `data/` changes, a third robot (`.github/workflows/pages.yml`) republishes the
   website automatically. `index.html` never needs to change again — it just reads whatever is
   in `data/*.json`.

You never run anything by hand. If you want to force an update right now instead of waiting for
the schedule, see "Running it manually" below.

## One-time setup (do this once)

### 1. Add your Groq API key as a GitHub secret
This lets the robot use the AI without the key ever appearing in the code.
1. Go to your repo on github.com → **Settings** → **Secrets and variables** → **Actions**.
2. Click **New repository secret**.
3. Name: `GROQ_API_KEY`. Value: paste your key (starts with `gsk_...`).
4. Click **Add secret**.

### 2. Turn on GitHub Pages
1. Go to **Settings** → **Pages**.
2. Under "Build and deployment", set **Source** to **GitHub Actions**.
3. That's it — no branch to pick, the `pages.yml` workflow handles it.

### 3. Push this code to GitHub
(Only needed once, to get the code from this computer onto GitHub.) See the commands your
assistant runs for you, or ask it to push for you.

### 4. Run it once manually to check it works
1. Go to the **Actions** tab on your repo.
2. Click **Daily data update** in the left list → **Run workflow** → **Run workflow**.
3. Wait ~1-2 minutes, then check the **Actions** tab for a green checkmark.
4. Go to **Settings → Pages** — it'll show your live site URL, something like
   `https://chhunlang.github.io/khemera-market-intel/`.

## Running it manually
Go to the **Actions** tab → pick a workflow (**Daily data update** or **Weekly and monthly
executive summaries**) → **Run workflow**. Useful for testing or if you want fresh data before
the scheduled time.

## Cost
Roughly **$1-3/month** in Groq API usage at typical volume (10-15 short articles/day). Groq's
free tier may cover this entirely depending on your plan — check console.groq.com/settings/billing.
GitHub Actions and Pages are free for public repositories.

## Known limitations (be aware of these)

- **Phnom Penh Post and Ministry of Commerce (moc.gov.kh) are not scraped.** Both sites blocked
  every automated request during setup (HTTP 403), including robots.txt itself — a strong signal
  they don't want automated access. Their stories are usually still picked up indirectly when
  Khmer Times, Kampuchea Thmey, or Construction & Property report the same news.
- **HTML-scraped sources (no RSS feed) use a best-effort generic extractor.** Cambodianess,
  Construction & Property, B2B Asia News, realestate.com.kh, Open Development Cambodia, and the
  Ministry of Mines & Energy newsroom don't publish RSS, so the scraper looks for headline-shaped
  links on their pages. If a source's website redesigns itself, that source's items may stop
  appearing — check the Actions log for `[scrape] <source> FAILED` to spot this, and tell your
  assistant which source broke so the selector in `scripts/common.py` can be fixed.
- **AI summaries can be wrong.** Always spot-check before using in an external-facing document.
  The "what this means for CBM" analysis is grounded in the scraped article, but the AI can still
  misread a number or nuance.
- **No live commodity price chart.** The original mockup's Brent/WTI price chart isn't
  reproduced since we don't have a live, reliable price-feed source wired up — the Oil & Energy
  category card still summarizes real oil-related news items instead.

## Project structure
```
index.html                          the website (design never needs to change)
data/daily.json                     rolling ~14 days of items the site reads
data/weekly.json / monthly.json     the latest executive summaries
data/archive/YYYY-MM-DD.json        permanent daily archives (source of truth for summaries)
data/seen_urls.json                 dedupe list so articles aren't processed twice
scripts/common.py                   source list, categories, pillars, file paths
scripts/scrape.py                   fetches raw headlines from each source
scripts/enrich.py                   AI-tags one item (category/scope/impact/summary/analysis)
scripts/summarize.py                AI-writes the weekly/monthly narrative around real stats
scripts/build_daily.py              daily orchestrator
scripts/build_weekly_monthly.py     weekly/monthly orchestrator
.github/workflows/daily.yml         runs build_daily.py every day
.github/workflows/weekly-monthly.yml runs build_weekly_monthly.py weekly + monthly
.github/workflows/pages.yml         republishes the site whenever data/ changes
```

## Adding or fixing a news source
Tell your assistant which source to add/fix and, if you have it, the exact RSS feed URL or the
news-listing page URL. Everything else (category tagging, summaries) works the same regardless
of source.
