# ============================== #
#      CONSTANTS & MAPPINGS      #
# ============================== #

# Mapping of stats to their corresponding column indices in the game stats table
AVAILABLE_STATS = {
    'points': 30,
    'assists': 25,
    'rebounds': 24,
    'steals': 26,
    'blocks': 27,
    '3pm': 12,
    'points_rebounds_assists': None, #Derived
    'points_assists': None, #Derived
    'points_rebounds': None, #Derived
    'rebounds_assists': None #Derived
}

# In modules/constants.py
STAT_NAME_MAPPING = {
    "game_date": "Game Date",
    "opponent": "Opponent",
    "result": "Result",
    "points": "Points",
    "assists": "Assists",
    "rebounds": "Rebounds",
    "steals": "Steals",
    "blocks": "Blocks",
    "3pm": "3PM",
    "points_rebounds_assists": "Points + Rebounds + Assists",
    "points_assists": "Points + Assists",
    "points_rebounds": "Points + Rebounds",
    "rebounds_assists": "Rebounds + Assists"
}

# Mapping of full team names to 3-letter team codes
TEAM_CODES = {
    'Atlanta Hawks': 'ATL',
    'Boston Celtics': 'BOS',
    'Brooklyn Nets': 'BRK',
    'Charlotte Hornets': 'CHO',
    'Chicago Bulls': 'CHI',
    'Cleveland Cavaliers': 'CLE',
    'Dallas Mavericks': 'DAL',
    'Denver Nuggets': 'DEN',
    'Detroit Pistons': 'DET',
    'Golden State Warriors': 'GSW',
    'Houston Rockets': 'HOU',
    'Indiana Pacers': 'IND',
    'Los Angeles Clippers': 'LAC',
    'Los Angeles Lakers': 'LAL',
    'Memphis Grizzlies': 'MEM',
    'Miami Heat': 'MIA',
    'Milwaukee Bucks': 'MIL',
    'Minnesota Timberwolves': 'MIN',
    'New Orleans Pelicans': 'NOP',
    'New York Knicks': 'NYK',
    'Oklahoma City Thunder': 'OKC',
    'Orlando Magic': 'ORL',
    'Philadelphia 76ers': 'PHI',
    'Phoenix Suns': 'PHO',
    'Portland Trail Blazers': 'POR',
    'Sacramento Kings': 'SAC',
    'San Antonio Spurs': 'SAS',
    'Toronto Raptors': 'TOR',
    'Utah Jazz': 'UTA',
    'Washington Wizards': 'WAS'
}

# List of common suffixes to remove from names for URL fetching
SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}