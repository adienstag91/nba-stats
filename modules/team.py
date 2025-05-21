# modules/team.py

from bs4 import BeautifulSoup
from modules.constants import TEAM_CODES
from modules.cache import safe_request
from modules.utils import *
from modules.player import Player

class Team:
    def __init__(self, name, season):
        self.name = name
        self.season = season
        self.code = TEAM_CODES.get(name)
        self.logo_url = None
        self.roster = []

        if self.code:
            self._fetch_team_page()
        else:
            print(f"❌ Team code for {name} not found.")

    def _fetch_team_page(self):
        url = f"https://www.basketball-reference.com/teams/{self.code}/{self.season}.html"
        response_text = safe_request(url, category="rosters")

        if not response_text:
            print(f"❌ Failed to fetch page for {selfame}")
            return

        soup = BeautifulSoup(response_text, "html.parser")

        # Extract logo
        media_item = soup.find("div", class_="media-item")
        img_tag = media_item.find("img") if media_item else None
        self.logo_url = img_tag["src"] if img_tag else None

        # Extract roster
        roster_table = soup.find("table", {"class": "sortable stats_table"})
        if roster_table:
            self.roster = [
                Player(format_display_name(row.find("td", {"data-stat": "player"}).get_text(strip=True)), self.name, self.season)
                for row in roster_table.find_all("tr")[1:]
                if row.find("td", {"data-stat": "player"})
            ]
        else:
            print(f"⚠️ No roster found for {self.name}")

    def get_player_names(self):
        return self.roster

    def __repr__(self):
        return f"<Team: {self.name}, Players: {len(self.roster)}>"
