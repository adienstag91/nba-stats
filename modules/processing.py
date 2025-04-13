import requests
from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd
from datetime import datetime, date
from modules.utils import *
from modules.constants import *
from modules.fetch import *
from modules.cache import *



# Function to calculate averages for stats
def calculate_averages(games):
    totals = {stat: 0 for stat in AVAILABLE_STATS}  # Initialize all stats to 0
    valid_game_count = 0  # To keep track of how many valid games we have

    for game in games:
        for stat in AVAILABLE_STATS:
            try:
                stat_value = game[stat]
                stat_value = float(stat_value) if stat_value else 0
                totals[stat] += stat_value
            except ValueError:
                print(f"Skipping invalid stat value: {game[stat]} for {stat}")
                continue
        
        valid_game_count += 1
    
    if valid_game_count == 0:
        return {}  # Prevent division by zero if no valid games are found
    
    # Calculate averages for each stat, rounded to 1 decimal place
    averages = {}
    for stat, total in totals.items():
        averages[f'avg_{stat}'] = round(total / valid_game_count, 1)

    return averages

# Function to get the last N games' stats
def get_last_n_games_stats(player_name, selected_date, stats, n=5):
    if not stats:
        return []

    print(datetime)
    # Convert game dates to datetime objects for comparison
    for game in stats:
        game["game_date"] = datetime.strptime(game["game_date"], "%Y-%m-%d").date()

    # Filter games that occurred **before or on** the selected date
    filtered_games = [game for game in stats if game["game_date"] <= selected_date]

    if not filtered_games:
        return [], {}

    # Get the last N games before the selected date
    last_n_games = filtered_games[-n:]
    
    # Reconvert dates to string format for display
    for game in last_n_games:
        game["game_date"] = game["game_date"].strftime("%Y-%m-%d")

    avg_stats = calculate_averages(last_n_games)
    
    return last_n_games, avg_stats

# Function to get full season averages
def get_full_season_averages(player_name, selected_date, stats):
    if not stats:
        return {}

    return calculate_averages(stats)

# Function to get stats against a specific opponent
def get_stats_against_opponent(player_name, player_team, year, stats, selected_game):

    if selected_game is None:
        return None, None, None  # Return empty values to avoid errors

    if not stats:
        print(f"No stats found for {player_name} in {year}.")
        return [], {}

    if player_team == selected_game['home_team']:
        opponent_team_name = selected_game['away_team']
    elif player_team == selected_game['away_team']:
        opponent_team_name = selected_game['home_team']
    else:
        print(f"Player {player_name} not found in either team's roster.")
        return [], {}

    opponent_team_code = TEAM_CODES[opponent_team_name]
    opponent_stats = [game for game in stats if game['opponent'] == opponent_team_code]

    if not opponent_stats:
        print(f"No games found against {selected_game['home_team']} or {selected_game['away_team']}.")
        return [], {}, opponent_team_name

    avg_opponent_stats = calculate_averages(opponent_stats)

    return opponent_stats, avg_opponent_stats, opponent_team_name

# Function to count how many times a stat exceeds a threshold
def count_exceeding_threshold(player_name, stat_type, threshold, stats):
    if not stats:
        return 0, 0, 0, 0, 0

    count_exceeded = sum(1 for game in stats if float(game[stat_type]) >= threshold)
    count_not_exceeded = len(stats) - count_exceeded
    total_games = len(stats)
    percentage_exceeded = (count_exceeded / total_games) * 100 if total_games > 0 else 0
    percentage_not_exceeded = (count_not_exceeded / total_games) * 100 if total_games > 0 else 0

    return count_exceeded, count_not_exceeded, total_games, percentage_exceeded, percentage_not_exceeded

def filter_stats(stats_data, selected_stats, is_average=False):
    """
    Filters the given stats dictionary/list based on selected stats.

    - stats_data: Dictionary (season averages) or list of dictionaries (last 5 games).
    - selected_stats: List of stat keys to keep.
    - is_average: If True, modifies keys to match the "avg_" prefix.

    Returns:
      - Filtered list of dictionaries (if stats_data is a list)
      - Filtered dictionary (if stats_data is a dictionary)
    """
    if isinstance(stats_data, list):  # Handling list (e.g., Last 5 Games)
        filtered_data = []
        for game in stats_data:
            filtered_game = {stat: game.get(stat, "N/A") for stat in selected_stats}
            filtered_game["game_date"] = game["game_date"]  # Keep game date
            filtered_data.append(filtered_game)
        return filtered_data

    elif isinstance(stats_data, dict):  # Handling dict (e.g., Season Averages, Last 5 Game Averages)
        if is_average:
            return {f"avg_{stat}": stats_data.get(f"avg_{stat}", "N/A") for stat in selected_stats}
        return {stat: stats_data.get(stat, "N/A") for stat in selected_stats}

    return stats_data  # If unexpected type, return as is

