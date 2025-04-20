import requests
from datetime import datetime, date
import time
from bs4 import BeautifulSoup, Comment
from modules.constants import *
from modules.utils import *
from modules.cache import *

def get_games_for_date(selected_date):
    """Fetch all games for a given date from Basketball Reference."""
    month = selected_date.strftime('%B').lower()
    year = selected_date.year
    url = f"https://www.basketball-reference.com/leagues/NBA_{year}_games-{month}.html"
    response_text = safe_request(url)

    if not response_text:
        print(f"❌ Failed to retrieve games for {selected_date}")
        return []

    soup = BeautifulSoup(response_text, 'html.parser')
    games = soup.find_all('table', {'id': 'schedule'})

    if not games:
        print(f"⚠️ No games found for {selected_date}.")
        return []

    game_list = []
    for game in games:
        for row in game.find_all('tr')[1:]:
            game_columns = row.find_all('td')
            if len(game_columns) > 3:
                game_date_str = row.find('th', {'data-stat': 'date_game'}).text.strip()
                try:
                    game_date = datetime.strptime(game_date_str, '%a, %b %d, %Y').date()
                except ValueError:
                    continue
                
                if game_date == selected_date:
                    home_team = game_columns[3].find('a').text.strip() if game_columns[3].find('a') else "Unknown"
                    away_team = game_columns[1].find('a').text.strip() if game_columns[1].find('a') else "Unknown"
                    game_time = game_columns[0].text.strip() if len(game_columns) > 3 else "Time Not Available"

                    game_list.append({
                        'home_team': home_team,
                        'away_team': away_team,
                        'game_time': game_time,
                        'game_date': game_date
                    })

    return game_list

def get_all_teams():
    """Return all team names."""
    return list(TEAM_CODES.keys())

def get_team_roster(team_name):
    """Fetch and cache a team's roster from Basketball Reference."""
    team_code = TEAM_CODES.get(team_name)
    if not team_code:
        print(f"❌ Team code for {team_name} not found.")
        return []

    url = f"https://www.basketball-reference.com/teams/{team_code}/2025.html"
    response_text = safe_request(url, category="rosters")

    if not response_text:
        print(f"❌ Failed to retrieve roster for {team_name}")
        return []

    soup = BeautifulSoup(response_text, 'html.parser')
    roster_table = soup.find('table', {'class': 'sortable stats_table'})

    if not roster_table:
        print(f"⚠️ No roster table found for {team_name}")
        return []

    roster = [
        (format_display_name(row.find('td', {'data-stat': 'player'}).get_text(strip=True)), team_name)
        for row in roster_table.find_all('tr')[1:]
        if row.find('td', {'data-stat': 'player'})
    ]

    return roster

def get_all_players_in_game(selected_game):
    """Fetch rosters for both teams in a selected game."""
    return get_team_roster(selected_game['home_team']) + get_team_roster(selected_game['away_team'])

def get_all_active_players():
    """Fetch and cache all active NBA players."""
    cache = load_cache()
    if "all_players" in cache and (time.time() - cache["all_players"].get("timestamp", 0)) < CACHE_EXPIRY["all_players"]:
        print("✅ Using cached all_players list")
        return cache["all_players"]["data"]

    print("🌍 Fetching all active players...")
    all_players = [player for team in get_all_teams() for player in get_team_roster(team)]
    
    cache["all_players"] = {"data": all_players, "timestamp": time.time()}
    save_cache(cache)
    return all_players

def get_team_logo(team_name):
    """Fetch and cache a team's logo from Basketball Reference."""
    team_code = TEAM_CODES.get(team_name)
    if not team_code:
        print(f"❌ Team code for {team_name} not found.")
        return None

    url = f"https://www.basketball-reference.com/teams/{team_code}/2025.html"
    response_text = safe_request(url, category="rosters")

    if not response_text:
        print(f"❌ Failed to retrieve team page for {team_name}")
        return None

    soup = BeautifulSoup(response_text, 'html.parser')

    # Extract team logo
    media_item_div = soup.find("div", class_="media-item")  # Look for media-item logo div first
    img_tag = media_item_div.find("img") if media_item_div else None  # Only search for <img> if div exists
    team_img_url = img_tag["src"] if img_tag else None  # Extract image URL if <img> exists

    return team_img_url