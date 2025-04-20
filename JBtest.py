from modules.player import Player
from modules.player import Player
from datetime import date

player = Player("Jalen Brunson", "New York Knicks", 2025)

if player.profile_url:
    print("Profile URL:", player.profile_url)
    print("Image URL:", player.image_url)

    if player.fetch_stats():
        print(player.stats[-2:])  # ✅ access the data directly from the object
        print(player.get_last_n_games(5,date.today()))
    else:
        print("No stats available.")
else:
    print("Player not found.")


