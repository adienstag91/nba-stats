from bs4 import BeautifulSoup
from datetime import datetime, date
from modules.cache import safe_request
from modules.utils import normalize_player_name, format_display_name
from modules.constants import *

class Player:
    def __init__(self, name, team, year):
        self.name = name
        self.team_name = team
        self.team_code = TEAM_CODES.get(self.team_name)
        self.year = year
        self.normalized_name = normalize_player_name(name)
        self.profile_url = None
        self.stats_url = None
        self.image_url = None
        self.stats = None
        self._urls_resolved = False  # ✅ Flag to track if URLs were resolved

    def _resolve_urls(self):
        if self._urls_resolved:
            return True

        BASE_URL = "https://www.basketball-reference.com/players/{}/{}"
        name_parts = self.normalized_name.split()
        last_name = name_parts[-1].lower()
        first_name = name_parts[0].lower().replace(".", "")
        first_five_last = last_name[:5]
        first_two_first = first_name[:2]
        first_letter = last_name[0]

        for i in range(1, 9):  # Try 01 to 08
            player_id = f"{first_five_last}{first_two_first}{str(i).zfill(2)}"
            profile_url = BASE_URL.format(first_letter, f"{player_id}.html")
            stats_url = BASE_URL.format(first_letter, f"{player_id}/gamelog/{self.year}")
            response = safe_request(profile_url)

            if not response:
                continue

            soup = BeautifulSoup(response, "html.parser")

            h1_tag = soup.find("h1")
            if not h1_tag or not h1_tag.find("span"):
                continue

            fetched_name = h1_tag.find("span").text.strip()
            if normalize_player_name(format_display_name(fetched_name)) != self.normalized_name:
                continue

            team_element = None
            for strong_tag in soup.select("#meta strong"):
                if "Team" in strong_tag.text:
                    team_element = strong_tag.find_next("a")
                    break
            fetched_team = team_element.text.strip() if team_element else None

            if fetched_team != self.team_name:
                continue

            self.profile_url = profile_url
            self.stats_url = stats_url

            media_item = soup.find("div", class_="media-item")
            img_tag = media_item.find("img") if media_item else None
            self.image_url = img_tag["src"] if img_tag else None
            self._urls_resolved = True  # ✅ Mark as resolved
            return True

        return False

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return self.__str__()

    def fetch_stats(self):
        if self.stats:
            return self.stats

        if not self._urls_resolved and not self._resolve_urls():
            print(f"⚠️ Could not resolve URLs for {self.name}")
            return None

        if not self.stats_url:
            print(f"⚠️ No stats URL found for {self.name}")
            return None

        response = safe_request(self.stats_url)
        if not response:
            print(f"❌ Failed to fetch stats page: {self.stats_url}")
            return None

        soup = BeautifulSoup(response, "html.parser")
        stats = []
        for table_id, game_type in [("player_game_log_reg", "regular"), ("player_game_log_post", "playoff")]:
            table = soup.find("table", {"id": table_id})
            if table:
                stats.extend(self._parse_stats_table(table, game_type))

        stats.sort(key=lambda x: x["game_date"])
        self.stats = stats
        return stats

    def _parse_stats_table(self, table, game_type):
        rows = table.find_all("tr")[1:]
        stats_list = []

        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 27:
                continue

            game_date = cols[2].get_text().strip()
            if not game_date or game_date.lower() in ["totals", ""]:
                continue

            stat_row = {
                "game_date": game_date,
                "opponent": cols[5].get_text(),
                "result": cols[6].get_text(),
                "game_type": game_type
            }

            for stat, idx in AVAILABLE_STATS.items():
                if idx is None:
                    continue  # Skip stats without a valid index
                try:
                    value = cols[idx].get_text()
                    stat_row[stat] = int(value) if value.isdigit() else float(value or 0)
                except (ValueError, IndexError):
                    stat_row[stat] = 0

            # Combo stats
            stat_row["points_rebounds"] = stat_row["points"] + stat_row["rebounds"]
            stat_row["points_assists"] = stat_row["points"] + stat_row["assists"]
            stat_row["rebounds_assists"] = stat_row["rebounds"] + stat_row["assists"]
            stat_row["points_rebounds_assists"] = stat_row["points"] + stat_row["rebounds"] + stat_row["assists"]

            stats_list.append(stat_row)

        return stats_list

    def _calculate_average_stats(self, games):
        """Return a dict of average stats across provided games."""
        if not games:
            return {}

        totals = {stat: 0 for stat in AVAILABLE_STATS}
        for game in games:
            for stat in AVAILABLE_STATS:
                totals[stat] += game.get(stat, 0)

        averages = {f"avg_{stat}": round(val / len(games), 1) for stat, val in totals.items()}
        return averages

    def get_season_averages(self):
        """Return full-season averages (all games)."""
        return self._calculate_average_stats(self.stats)

    def get_last_n_games(self, n=5, selected_date=None):
        """Returns the last n games before a specified date (inclusive)."""
        if not self.stats:
            print("⚠️ No stats loaded. Call fetch_stats() first.")
            return []

        if selected_date:
            filtered_games = [g for g in self.stats if datetime.strptime(g["game_date"], "%Y-%m-%d").date() <= selected_date]
        else:
            filtered_games = self.stats[:]

        last_n_games = filtered_games[-n:]  # Last n games before date
        avg_over_last_n_games = self._calculate_average_stats(last_n_games)

        return last_n_games, avg_over_last_n_games

    def get_stats_against_opponent(self, opponent_team_code):
        """Return games and averages against a specific opponent."""
        #if not self.stats:
         #   return [], {}

        games_vs_opponent = [g for g in self.stats if g["opponent"] == opponent_team_code]
        avg_vs_opponent = self._calculate_average_stats(games_vs_opponent)

        return games_vs_opponent, avg_vs_opponent

    def count_exceeding_threshold(self, stat, threshold):
        """
        Count how many games exceed a stat threshold.
        Returns: (count_exceeded, count_not_exceeded, total_games, pct_exceeded, pct_not_exceeded)
        """
        if not self.stats:
            return (0, 0, 0, 0.0, 0.0)

        count_exceeded = 0
        for game in self.stats:
            if game.get(stat, 0) >= threshold:
                count_exceeded += 1

        total_games = len(self.stats)
        count_not_exceeded = total_games - count_exceeded
        pct_exceeded = (count_exceeded / total_games) * 100 if total_games else 0
        pct_not_exceeded = 100 - pct_exceeded

        return (count_exceeded, count_not_exceeded, total_games, pct_exceeded, pct_not_exceeded)

