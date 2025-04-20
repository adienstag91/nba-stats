from modules.player import Player
from datetime import date

player = Player("Stephen Curry", "Golden State Warriors", 2025)
if player.fetch_stats():
    print(player.get_season_averages())
    print(player.get_last_n_games())
    print(player.get_games_against_opponent("LAC"))
    print(player.count_exceeding_threshold("points", 30))