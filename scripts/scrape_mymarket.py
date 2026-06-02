"""
mymarket.ge Construction Materials Price Scraper
================================================
Scrapes all listings from:
  https://mymarket.ge/ka/search/2815/mshenebloba-da-remonti/samsheneblo-masalebi

Methodology
-----------
mymarket.ge is a JavaScript-rendered (Next.js) marketplace — plain HTTP requests
return 403. We use Playwright to drive a real browser, navigate each of the 25
pages, extract article cards from the DOM, and persist unique items via the
browser's localStorage so state survives cross-page navigation.

After scraping, prices are grouped by material category, median prices computed,
and the SQLite database is updated via seed_prices.py.

Usage
-----
    pip install playwright
    playwright install chromium
    python scripts/scrape_mymarket.py [--pages 25] [--out data/mymarket_raw.json]

Output
------
  data/mymarket_raw.json   — all scraped items {name, price, page}
  data/mymarket_prices.json — category medians used to update DB

Requirements: playwright>=1.40.0
"""
import argparse
import json
import os
import statistics
import time
from pathlib import Path

# ─── Georgian keyword → English category mapping ─────────────────────────────

CATEGORY_MAP = [
    ("concrete",       ["ბეტონი", "M200", "M300", "M400"]),
    ("cement",         ["ცემენტი", "ცემენტ"]),
    ("brick",          ["აგური"]),
    ("block",          ["ბლოკი", "ბლოკ", "გაზობლოკ", "პემზის ბლოკ"]),
    ("aggregate",      ["ქვიშა", "ხრეში", "ღორღ", "პემზა"]),
    ("rebar",          ["არმატურ", "A400", "A500", "სარმატ"]),
    ("insulation",     ["ვათა", "ვატა", "იზოლ", "პენოპ", "პოლისტ", "XPS", "ქვა ბამბ"]),
    ("roofing",        ["სახურავ", "შიფერ", "ონდულ", "კრამიტ"]),
    ("waterproofing",  ["ჰიდრო", "ბიტუმ"]),
    ("tile",           ["ფილა", "კრამიტ", "კერამიკ"]),
    ("plaster",        ["შტუკ", "გიფს", "ბათქაშ"]),
    ("paint",          ["საღებავ", "ლაქ"]),
    ("window",         ["ფანჯარ"]),
    ("door",           ["კარი ", "კარ-"]),
    ("adhesive",       ["წებო-ცემ", "წებო"]),
    ("lumber",         ["ფიცარ", "ხე-ტყ", "დაფ"]),
]

# Labels we filter out (badge types, condition words, seller type words)
SKIP_WORDS = {
    "S-VIP", "VIP+", "VIP",
    "ახალი", "მეორადი", "გამოყენებული",
    "ფიზიკური პირი", "მიტანით",
}

# ─── Playwright scraper ───────────────────────────────────────────────────────

HARVEST_JS = r"""
(pageNum) => {
  const SKIP = new Set(%s);
  let stored = JSON.parse(localStorage.getItem('_mkItems') || '[]');
  let seen   = new Set(stored.map(i => i.name + '|' + i.price));
  let added  = 0;

  document.querySelectorAll('article').forEach(article => {
    const txt = article.innerText.trim();
    if (!txt.includes('₾')) return;

    const lines = txt.split('\n').map(l => l.trim()).filter(Boolean);
    const priceIdx = lines.findIndex(l => l.includes('₾'));
    if (priceIdx < 0) return;

    const pm = lines[priceIdx].match(/([\d ]+[.,]\d{2})\s*₾/);
    if (!pm) return;
    const price = parseFloat(pm[1].replace(/\s/g, '').replace(',', '.'));

    // Walk backwards from the price line to find the product name
    let name = '';
    for (let i = priceIdx - 1; i >= 0; i--) {
      const l = lines[i];
      if (
        !SKIP.has(l) &&
        !l.match(/^[\d.,\s]+₾/) &&
        l.length > 2 &&
        !l.includes('LTD') &&
        !l.includes('LLC') &&
        !l.includes('•') &&
        !l.match(/^\d+$/)
      ) {
        name = l;
        break;
      }
    }

    if (!name || price <= 0) return;
    const key = name + '|' + price;
    if (!seen.has(key)) {
      seen.add(key);
      stored.push({ name, price, page: pageNum });
      added++;
    }
  });

  localStorage.setItem('_mkItems', JSON.stringify(stored));
  return { total: stored.length, added };
}
""" % json.dumps(list(SKIP_WORDS))


def scrape(total_pages: int = 25, headless: bool = True) -> list[dict]:
    """Navigate all pages and return collected items."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit(
            "Playwright not installed.\n"
            "Run:  pip install playwright && playwright install chromium"
        )

    base_url = (
        "https://mymarket.ge/ka/search/2815"
        "/mshenebloba-da-remonti/samsheneblo-masalebi"
        "?CatID=2815&Page={page}"
    )

    items: list[dict] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="ka-GE",
        )
        page = context.new_page()

        # Clear any stale localStorage on first load
        page.goto(base_url.format(page=1), wait_until="domcontentloaded")
        page.evaluate("localStorage.removeItem('_mkItems')")

        for pg in range(1, total_pages + 1):
            url = base_url.format(page=pg)
            print(f"  Page {pg:>2}/{total_pages}  {url}")

            if pg > 1:
                page.goto(url, wait_until="domcontentloaded")

            # Wait for article cards to appear
            try:
                page.wait_for_selector("article", timeout=8_000)
            except Exception:
                print(f"    ⚠  No articles found on page {pg}, skipping")
                continue

            result = page.evaluate(HARVEST_JS, pg)
            print(f"    → +{result['added']} new items  (total {result['total']})")
            time.sleep(0.4)   # polite crawl delay

        # Pull final dataset from localStorage
        raw = page.evaluate("JSON.parse(localStorage.getItem('_mkItems') || '[]')")
        items = raw

        browser.close()

    print(f"\n✅ Scraped {len(items)} unique items across {total_pages} pages")
    return items


# ─── Price processing ─────────────────────────────────────────────────────────

def categorise(items: list[dict]) -> dict[str, list[float]]:
    """Map each item to a category and collect its price."""
    buckets: dict[str, list[float]] = {}
    for item in items:
        name_lower = item["name"].lower()
        cat = "other"
        for category, keywords in CATEGORY_MAP:
            if any(kw.lower() in name_lower for kw in keywords):
                cat = category
                break
        buckets.setdefault(cat, []).append(item["price"])
    return buckets


def compute_medians(buckets: dict[str, list[float]]) -> dict[str, dict]:
    """Return per-category median, min, max, and count."""
    summary = {}
    for cat, prices in sorted(buckets.items()):
        if cat == "other":
            continue
        clean = [p for p in prices if p > 0]
        if not clean:
            continue
        summary[cat] = {
            "count":  len(clean),
            "median": round(statistics.median(clean), 2),
            "mean":   round(statistics.mean(clean), 2),
            "min":    min(clean),
            "max":    max(clean),
        }
    return summary


# ─── Entry point ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Scrape mymarket.ge construction materials")
    parser.add_argument("--pages",   type=int, default=25, help="Number of pages to scrape (default: 25)")
    parser.add_argument("--out",     default="data/mymarket_raw.json",    help="Raw output path")
    parser.add_argument("--summary", default="data/mymarket_prices.json", help="Category medians output path")
    parser.add_argument("--headed",  action="store_true", help="Run browser in headed (visible) mode")
    args = parser.parse_args()

    # ── 1. Scrape ──────────────────────────────────────────────────────────────
    print(f"\n🔍 Scraping mymarket.ge — up to {args.pages} pages …\n")
    items = scrape(total_pages=args.pages, headless=not args.headed)

    # ── 2. Save raw data ───────────────────────────────────────────────────────
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(items, ensure_ascii=False, indent=2))
    print(f"📄 Raw data saved → {out_path}  ({len(items)} records)")

    # ── 3. Compute category medians ────────────────────────────────────────────
    buckets = categorise(items)
    summary = compute_medians(buckets)

    summary_path = Path(args.summary)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"📊 Price summary saved → {summary_path}\n")

    # ── 4. Print table ─────────────────────────────────────────────────────────
    print(f"{'Category':<20} {'Count':>5}  {'Median (GEL)':>12}  {'Min':>8}  {'Max':>8}")
    print("─" * 60)
    for cat, stats in summary.items():
        print(
            f"{cat:<20} {stats['count']:>5}  "
            f"{stats['median']:>12.2f}  "
            f"{stats['min']:>8.2f}  "
            f"{stats['max']:>8.2f}"
        )

    print("\n✅ Done. Import results into the database with:")
    print("   python backend/database/seed_prices.py\n")


if __name__ == "__main__":
    main()
