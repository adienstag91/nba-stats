import json
import time
import os
import requests
from playwright.sync_api import sync_playwright

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


def safe_request(url, category="pages", max_retries=3):
    """
    Fetches data from the given URL, caches the result, and handles errors.
    Cached data expires based on the category's expiry time.
    """
    cache = load_cache()
    category_cache = cache.get(category, {})

    # Ensure cache stores structured data (handle old raw string cache)
    cached_entry = cache.get(url)
    if isinstance(cached_entry, str):  
        # Convert old cache format (raw HTML) to new format (dict with timestamp)
        print(f"⚠️ Converting old cache format for {url}")
        cache[url] = {"data": cached_entry, "timestamp": time.time()}
        save_cache(cache)

    # Check if cached response exists and is still valid
    if url in category_cache:
        timestamp = category_cache[url].get("timestamp", 0)
        age = time.time() - timestamp

        if age < CACHE_EXPIRY[category]:
            print(f"✅ Using cached {category} response for {url} (Age: {age / 3600:.2f} hours)")
            return category_cache[url]["data"]

        print(f"⏳ Cache expired for {category} {url}. Fetching fresh data.")

    print(f"🌍 Fetching {url} from the internet...")

    # Retry mechanism
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()

            if response.text.strip():  # Ensure response isn't empty
                category_cache[url] = {
                    "data": response.text,
                    "timestamp": time.time()
                }
                cache[category] = category_cache
                save_cache(cache)
                print(f"✅ Cached response for {category} {url}")
                return response.text

        except requests.exceptions.RequestException as e:
            print(f"❌ Attempt {attempt + 1} failed: {e}")
            time.sleep(2)

    print(f"❌ Failed to fetch {url} after {max_retries} attempts.")
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
