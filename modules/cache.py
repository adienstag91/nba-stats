import json
import time
import os
import requests

CACHE_FILE = "nba_cache.json"
CACHE_EXPIRY = {
    "rosters": 7 * 24 * 60 * 60,  # 7 days
    "all_players": 7 * 24 * 60 * 60,  # 7 days
    "player_stats": 24 * 60 * 60,  # 1 day
    "pages": 12 * 60 * 60  # 12 hours
}

def load_cache():
    """Load the cache from file or return an empty structured cache."""
    if not os.path.exists(CACHE_FILE):
        return {"rosters": {}, "all_players": {}, "player_stats": {}, "pages": {}, "player_photos": {}}

    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("⚠️ Cache file is corrupted. Resetting cache.")
        return {"rosters": {}, "all_players": {}, "player_stats": {}, "pages": {}}

def save_cache(cache):
    """Save the cache to file."""
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=4)


from playwright.sync_api import sync_playwright

def safe_request(url, category="pages"):
    """
    Always uses Playwright to fetch the page, with full caching and expiry support.
    """
    cache = load_cache()
    category_cache = cache.get(category, {})

    # Use cached version if valid
    if url in category_cache:
        timestamp = category_cache[url].get("timestamp", 0)
        age = time.time() - timestamp
        if age < CACHE_EXPIRY[category]:
            print(f"✅ Using cached {category} response for {url} (Age: {age / 3600:.2f} hours)")
            return category_cache[url]["data"]
        else:
            print(f"⏳ Cache expired for {category} {url}. Fetching fresh data.")

    print(f"🌍 Fetching {url} using Playwright...")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=20000, wait_until="domcontentloaded")
            html = page.content()
            browser.close()

            if html.strip():
                category_cache[url] = {"data": html, "timestamp": time.time()}
                cache[category] = category_cache
                save_cache(cache)
                print(f"✅ Playwright fetch + cache successful for {url}")
                return html
            else:
                print(f"⚠️ Empty content received from Playwright for {url}")

    except Exception as e:
        print(f"❌ Playwright failed for {url}: {e}")

    return None

def clear_cache(category=None):
    """
    Clears the entire cache or a specific category.
    If category is None, clears all caches.
    """
    if category:
        cache = load_cache()
        if category in cache:
            cache[category] = {}
            save_cache(cache)
            print(f"🗑️ Cleared cache for {category}.")
        else:
            print(f"⚠️ Category '{category}' not found in cache.")
    else:
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
            print("🗑️ Cache file deleted.")
