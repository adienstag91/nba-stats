import requests
from datetime import datetime, date
import time
from bs4 import BeautifulSoup, Comment
from modules.constants import *
from modules.utils import *
from modules.cache import *
from modules.team import Team
from modules.game import Game

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

                    game_list.append(Game(home_team, away_team, game_date, game_time))

    return game_list

def get_all_teams():
    """Return all team names."""
    return list(TEAM_CODES.keys())

def get_all_players_in_game(selected_game):
    """Fetch rosters for both teams in a selected game."""
    home_team = Team(selected_game.home_team.name)
    away_team = Team(selected_game.away_team.name)

    return home_team.roster + away_team.roster

def get_all_active_players():
    """Fetch and cache all active NBA players."""
    cache = load_cache()
    if "all_players" in cache and (time.time() - cache["all_players"].get("timestamp", 0)) < CACHE_EXPIRY["all_players"]:
        print("✅ Using cached all_players list")
        return cache["all_players"]["data"]

    print("🌍 Fetching all active players...")
    all_players = []
    for team_name in TEAM_CODES:
        team = Team(team_name)
        all_players.extend(team.roster)
        time.sleep(7)
    
    cache["all_players"] = {"data": all_players, "timestamp": time.time()}
    save_cache(cache)
    return all_players
