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

def get_player_url(player_name, player_team, year):
    """Finds the correct Basketball-Reference player URL."""
    BASE_PLAYER_URL = "https://www.basketball-reference.com/players/{}/{}"

    normalized_name = normalize_player_name(player_name)
    name_parts = normalized_name.split()
    last_name = name_parts[-1].lower()
    first_name = name_parts[0].lower()
    first_name_clean = first_name.replace('.', '')

    first_letter_last_name = last_name[0]
    first_five_last_name = last_name[:5]
    first_two_first_name = first_name_clean[:2]
    
    for identifier in range(1, 9):  # Try identifiers from 01 to 08
        player_id = f"{first_five_last_name}{first_two_first_name}{str(identifier).zfill(2)}"
        player_profile_url = BASE_PLAYER_URL.format(first_letter_last_name, f"{player_id}.html")

        response_text = safe_request(player_profile_url)
        if not response_text:
            continue  # If the profile page doesn't exist, try the next identifier

        soup = BeautifulSoup(response_text, "html.parser")
        
        h1_tag = soup.find("h1")
        if h1_tag and h1_tag.find("span"):  # Ensure there's a <span> inside <h1>
            player_name_from_page = h1_tag.find("span").text.strip()
            formatted_player_name_from_page = format_display_name(player_name_from_page)
            normalized_player_name_from_page = normalize_player_name(formatted_player_name_from_page)

            # Extract the player's current team
            team_element = None
            for strong_tag in soup.select("#meta strong"):
                if "Team" in strong_tag.text:
                    team_element = strong_tag.find_next("a")  # Get the next <a> tag
                    break

            player_team_from_page = team_element.text.strip() if team_element else None

            if normalized_player_name_from_page == normalized_name and player_team_from_page == player_team:
                #Construct player stats URL
                player_stats_url = BASE_PLAYER_URL.format(first_letter_last_name, f"{player_id}/gamelog/{year}")
                #Extract player image URL
                media_item_div = soup.find("div", class_="media-item")  # Look for media-item div first
                img_tag = media_item_div.find("img") if media_item_div else None  # Only search for <img> if div exists
                player_img_url = img_tag["src"] if img_tag else None  # Extract image URL if <img> exists
                #print(f"✅ Found player profile URL: {player_profile_url}")
                #print(f"🔢 Found player stats URL: {player_stats_url}")
                #print(f"🖼 Player image URL: {player_img_url}")

                return player_profile_url, player_stats_url, player_img_url  # Return profile URL, game log URL, and image URL

    return None, None, None  # No match found

def get_player_stats(player_name, player_team, year):
    _,player_stats_url,_ = get_player_url(player_name, player_team, year)

    if not player_stats_url:
        print(f"⚠️ Player {player_name} not found.")
        return None

    #print(f"📡 Fetching stats for {player_name} from URL: {player_stats_url}")

    response_text = safe_request(player_stats_url)

    if not response_text:
        print(f"❌ Failed to fetch player page: {player_stats_url}")
        return None

    soup = BeautifulSoup(response_text, "html.parser")

    # Regular Season Stats
    stats = []
    regular_season_table = soup.find('table', {'id': 'player_game_log_reg'})
    if regular_season_table:
        stats.extend(extract_player_stats(regular_season_table, "regular"))

    # Playoff Stats
    playoff_table = soup.find('table', {'id': 'player_game_log_post'})
    if playoff_table:
        stats.extend(extract_player_stats(playoff_table, "playoff"))

    # Sort by date to ensure proper order
    stats.sort(key=lambda x: x['game_date'])  # Most recent games at bottom

    return stats  # ✅ Returning the stats list

def extract_player_stats(stats_table, game_type):
    """Extracts player stats from a given BeautifulSoup table."""
    if not stats_table:
        return []

    stats = []
    for row in stats_table.find_all('tr')[1:]:  # Skip header row
        game_stats = row.find_all('td')
        if len(game_stats) < 27:
            continue

        # Extract game date
        game_date = game_stats[2].get_text().strip()
        
        # Skip "Totals" row (it has no date)
        if not game_date or game_date.lower() in ["totals", ""]:
            continue

        game_data = {
            'game_date': game_stats[2].get_text(),
            'opponent': game_stats[5].get_text(),
            'result': game_stats[6].get_text(),
            'game_type': game_type  # ✅ Adding game_type (regular/playoff)
        }

        for stat, column_index in AVAILABLE_STATS.items():
            if column_index is not None:
                try:
                    game_data[stat] = int(game_stats[column_index].get_text() or 0)
                except ValueError:
                    game_data[stat] = float(game_stats[column_index].get_text() or 0)  # Handle percentages

        game_data['points_rebounds'] = game_data['points'] + game_data['rebounds']
        game_data['points_assists'] = game_data['points'] + game_data['assists']
        game_data['rebounds_assists'] = game_data['rebounds'] + game_data['assists']
        game_data['points_rebounds_assists'] = game_data['points'] + game_data['rebounds'] + game_data['assists']

        stats.append(game_data)

    return stats  # ✅ Returning extracted stats