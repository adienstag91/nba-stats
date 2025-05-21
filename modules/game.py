from modules.team import Team
from modules.utils import *

class Game:
    def __init__(self, home_team_name, away_team_name, game_date, game_time):
        self.game_date = game_date
        self.game_time = game_time
        self.season = get_season_year(self.game_date)
        self.home_team = Team(home_team_name, self.season)
        self.away_team = Team(away_team_name, self.season)

    def __str__(self):
        return f"{self.away_team.name} @ {self.home_team.name} on {self.game_date} at {self.game_time}"

    def get_all_players(self):
        return self.home_team.roster + self.away_team.roster
