import datetime
import requests
from bs4 import BeautifulSoup
from modules.cache import safe_request

def get_games_for_date(year, month, selected_date):
    """Fetch all games for a given date from Basketball Reference, using cached requests."""
    url = f"https://www.basketball-reference.com/leagues/NBA_{year}_games-{month}.html"
    response_text = safe_request(url)

    if not response_text:
        print(f"❌ Failed to retrieve or cache games page: {url}")
        return []

    soup = BeautifulSoup(response_text, 'html.parser')
    games = soup.find_all('table', {'id': 'schedule'})

    if not games:
        print(f"⚠️ No schedule table found for {year}-{month}.")
        return []

    game_list = []
    for game in games:
        game_info = game.find_all('tr')[1:]

        for row in game_info:
            game_columns = row.find_all('td')
            if len(game_columns) > 3:
                game_date_str = row.find('th', {'data-stat': 'date_game'}).text.strip()
                try:
                    game_date = datetime.datetime.strptime(game_date_str, '%a, %b %d, %Y').date()
                except ValueError:
                    continue
                
                if game_date == selected_date:
                    home_team = game_columns[3].find('a')
                    home_team_name = home_team.text.strip() if home_team else "Unknown"
                    away_team = game_columns[1].find('a')
                    away_team_name = away_team.text.strip() if away_team else "Unknown"
                    game_time = game_columns[0].text.strip() if len(game_columns) > 3 else "Time Not Available"

                    game_list.append({
                        'home_team': home_team_name,
                        'away_team': away_team_name,
                        'game_time': game_time,
                        'game_date': game_date
                    })

    return game_list
